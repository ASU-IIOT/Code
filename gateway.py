# gateway.py
#run together with edge.py in 2 terminals 
from flask import Flask, request, jsonify
import json
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"   # change to your LAN broker IP if needed
PORT   = 1883
DEVICE = "Machine1"

TOP_TELE = f"lab/telemetry/{DEVICE}"
TOP_CMD  = f"lab/cmd/{DEVICE}"

latest = None

def on_connect(c, u, f, rc):
    c.subscribe(TOP_TELE)

def on_message(c, u, msg):
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

app = Flask(__name__)

@app.get("/telemetry")
def get_telemetry():
    if latest is None:
        return jsonify({"error": "no data"}), 404
    return jsonify(latest)

@app.post("/command")
def send_command():
    cmd = request.get_json(force=True)  # e.g. {"setpoint": 25.0}
    mqttc.publish(TOP_CMD, json.dumps(cmd), qos=0)
    return jsonify({"status": "sent"}), 202

if __name__ == "__main__":
    app.run()  # http://127.0.0.1:5000
