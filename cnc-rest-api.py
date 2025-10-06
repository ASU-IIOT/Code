# app.py
from flask import Flask, request, jsonify
from datetime import datetime, timezone
from collections import defaultdict
import json

app = Flask(__name__)

# -------- In-memory storage --------
latest_by_device = {}                  # deviceId -> latest record (dict)
history_by_device = defaultdict(list)  # deviceId -> list of records
HISTORY_LIMIT = 100

# -------- Helpers --------
def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def read_json_or_error():
    """
    Robust JSON reader:
      1) Try Flask's parser (respects Content-Type)
      2) If that returns None, try json.loads(raw)
      3) If still nothing or invalid, return a detailed 400 payload
    """
    raw = request.get_data(as_text=True) or ""
    ct = request.headers.get("Content-Type", "")
    data = request.get_json(silent=True)  # won't throw; returns None if not JSON or empty

    if data is None and raw.strip():
        try:
            data = json.loads(raw)
        except Exception as e:
            return None, {
                "error": "Bad Request",
                "message": "Body is not valid JSON. In Postman: Body → raw → JSON.",
                "content_type": ct,
                "content_length": request.content_length or 0,
                "parse_error": str(e),
                "raw_preview": raw[:120],
            }

    if data is None:  # empty or not JSON
        return None, {
            "error": "Bad Request",
            "message": "Empty body or not JSON. In Postman: set Body → raw → JSON and Content-Type: application/json.",
            "content_type": ct,
            "content_length": request.content_length or 0,
        }

    return data, None

def validate_telemetry(payload: dict, partial=False) -> dict:
    """
    Validates and normalizes telemetry payload.
    For POST (partial=False): require deviceId & metrics.
    For PUT  (partial=True): allow partial updates; merge later.
    """
    if not isinstance(payload, dict):
        return None

    out = {}

    # Required for create
    if not partial:
        for field in ("deviceId", "metrics"):
            if field not in payload:
                return {"_error": f"Missing field: {field}"}

    device_id = payload.get("deviceId")
    if device_id is not None and not isinstance(device_id, str):
        return {"_error": "deviceId must be a string"}
    if device_id is not None:
        out["deviceId"] = device_id

    ts = payload.get("ts")
    if ts is None:
        ts = iso_now()
    elif not isinstance(ts, str):
        return {"_error": "ts must be an ISO 8601 string"}
    out["ts"] = ts

    if "metrics" in payload:
        metrics = payload["metrics"]
        if not isinstance(metrics, dict):
            return {"_error": "metrics must be an object"}
        try:
            # coerce all metric values to float
            metrics = {k: float(v) for k, v in metrics.items()}
        except Exception:
            return {"_error": "all metric values must be numbers"}
        out["metrics"] = metrics

    return out

# -------- Error handlers (JSON) --------
@app.errorhandler(404)
def not_found(_e):
    return jsonify(error="Not Found", message="Resource not found"), 404

@app.errorhandler(405)
def method_not_allowed(_e):
    return jsonify(error="Method Not Allowed", message="Check the HTTP method and route"), 405

@app.errorhandler(500)
def server_error(_e):
    return jsonify(error="Server Error", message="Unexpected error"), 500

# -------- Info / health --------
@app.get("/")
def root():
    return jsonify(
        name="CNC Telemetry API (demo)",
        endpoints={
            "POST": ["/api/telemetry"],
            "GET": [
                "/api/devices",
                "/api/devices/<deviceId>/telemetry/latest",
                "/api/devices/<deviceId>/telemetry?limit=N"
            ],
            "PUT": ["/api/devices/<deviceId>/telemetry/latest"],
            "DEBUG": ["/debug/echo"]
        }
    )

@app.get("/healthz")
def health():
    return jsonify(status="ok", devices=len(latest_by_device))

# -------- Debug endpoint to see what the server received --------
@app.post("/debug/echo")
def debug_echo():
    raw = request.get_data(as_text=True) or ""
    return jsonify(
        method=request.method,
        content_type=request.headers.get("Content-Type"),
        content_length=request.content_length or 0,
        raw_preview=raw[:200]
    )

# -------- REST endpoints --------
# Create a new telemetry record (becomes latest for that device)
@app.post("/api/telemetry")
def create_telemetry():
    data, err = read_json_or_error()
    if err:
        return jsonify(err), 400

    validated = validate_telemetry(data, partial=False)
    if not validated or "_error" in validated:
        return jsonify(error="Bad Request", message=validated.get("_error", "Invalid payload")), 400

    did = validated["deviceId"]
    latest_by_device[did] = validated
    history_by_device[did].append(validated)
    if len(history_by_device[did]) > HISTORY_LIMIT:
        history_by_device[did] = history_by_device[did][-HISTORY_LIMIT:]

    return jsonify(validated), 201

# List devices with last timestamp
@app.get("/api/devices")
def list_devices():
    devices = [{"deviceId": did, "lastTs": rec.get("ts")} for did, rec in latest_by_device.items()]
    return jsonify(devices)

# Get latest telemetry for a device
@app.get("/api/devices/<string:device_id>/telemetry/latest")
def get_latest(device_id):
    rec = latest_by_device.get(device_id)
    if not rec:
        return jsonify(error="Not Found", message=f"No telemetry for device {device_id}"), 404
    return jsonify(rec)

# Get last N records (default 10)
@app.get("/api/devices/<string:device_id>/telemetry")
def get_history(device_id):
    if device_id not in history_by_device:
        return jsonify(error="Not Found", message=f"No telemetry for device {device_id}"), 404
    try:
        limit = int(request.args.get("limit", 10))
    except ValueError:
        return jsonify(error="Bad Request", message="limit must be an integer"), 400
    limit = max(1, min(limit, HISTORY_LIMIT))
    return jsonify(history_by_device[device_id][-limit:])

# Update latest (partial). Merges metrics; refreshes ts if not provided.
@app.put("/api/devices/<string:device_id>/telemetry/latest")
def update_latest(device_id):
    current = latest_by_device.get(device_id)
    if not current:
        return jsonify(error="Not Found", message=f"No telemetry for device {device_id}"), 404

    data, err = read_json_or_error()
    if err:
        return jsonify(err), 400

    patch = validate_telemetry(data, partial=True)
    if not patch or "_error" in patch:
        return jsonify(error="Bad Request", message=patch.get("_error", "Invalid payload")), 400

    updated = current.copy()

    # deviceId changes are ignored to keep records under the same device
    patch.pop("deviceId", None)

    # merge metrics if provided
    if "metrics" in patch:
        merged = updated.get("metrics", {}).copy()
        merged.update(patch["metrics"])
        updated["metrics"] = merged

    # refresh timestamp if not provided
    updated["ts"] = patch.get("ts", iso_now())

    latest_by_device[device_id] = updated
    history_by_device[device_id].append(updated)
    if len(history_by_device[device_id]) > HISTORY_LIMIT:
        history_by_device[device_id] = history_by_device[device_id][-HISTORY_LIMIT:]

    return jsonify(updated)

# -------- Entry point --------
if __name__ == "__main__":
    # Bind to 0.0.0.0 if you want to hit it from other devices on your LAN
    app.run(host="127.0.0.1", port=5000, debug=True)
