# gateway.py
#run together with edge.py in 2 terminals 
from flask import Flask, request, jsonify
import json
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"   # change to your LAN broker IP if needed
PORT   = 1883
DEVICE = "Machine1"

# --- Topic names -----------------------------------------------------------
# Telemetry (edge → broker → gateway subscribes)
# Command   (gateway → broker → edge subscribes)

TOP_TELE = f"lab/telemetry/{DEVICE}"
TOP_CMD  = f"lab/cmd/{DEVICE}"

# --- In-memory cache -------------------------------------------------------
# Holds the most recent telemetry JSON seen by the gateway.

latest = None



def on_connect(c, u, f, rc):
    """Subscribe to telemetry after connecting to the broker."""
    c.subscribe(TOP_TELE)

def on_message(c, u, msg):
    """Update the in-memory 'latest' snapshot whenever telemetry arrives."""
    global latest
    try:
        latest = json.loads(msg.payload)
    except Exception:
        latest = None

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.connect(BROKER, PORT, 60)
mqttc.loop_start()

# --- Flask app -------------------------------------------------------------

app = Flask(__name__)

@app.get("/telemetry")
def get_telemetry():
    """
    Return the latest telemetry snapshot as JSON.
    200 with JSON if available; otherwise 404 with {"error":"no data"}.
    """
    if latest is None:
        return jsonify({"error": "no data"}), 404
    return jsonify(latest)

@app.post("/command")
def send_command():
    """
    Accept a JSON command and publish it to the device's command topic.
    Example body: { "setpoint": 25.0 }
    Returns 202 to indicate the command was accepted for publishing.
    """
    cmd = request.get_json(force=True)  # e.g. {"setpoint": 25.0}
    mqttc.publish(TOP_CMD, json.dumps(cmd), qos=0)
    return jsonify({"status": "sent"}), 202

if __name__ == "__main__":
    app.run()  # http://127.0.0.1:5000
