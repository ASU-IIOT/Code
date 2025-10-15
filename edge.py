# edge.py
import json, time, random
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"   # change to your LAN broker IP if needed
PORT   = 1883
DEVICE = "Machine1"

TOP_TELE = f"lab/telemetry/{DEVICE}"
TOP_CMD  = f"lab/cmd/{DEVICE}"

state = {"setpoint": 22.0}

# --- MQTT Callbacks --------------------------------------------------------

def on_connect(c, u, f, rc):
    """Subscribe to the command topic when the client connects."""
    c.subscribe(TOP_CMD)

def on_message(c, u, msg):
    try:
        cmd = json.loads(msg.payload)
        if "setpoint" in cmd:
            state["setpoint"] = float(cmd["setpoint"])
    except Exception:
        pass

# --- MQTT Client Setup -----------------------------------------------------

client = mqtt.Client()  # MQTT v3.1.1 (simple default)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_start()

# --- Main publish loop -----------------------------------------------------

try:
    while True:
        temp = round(state["setpoint"] + random.uniform(-1.5, 1.5), 2)
        vib  = round(random.uniform(0.0, 5.0), 2)
        payload = {"deviceId": DEVICE, "metrics": {"temp_c": temp, "vibration": vib}}
        client.publish(TOP_TELE, json.dumps(payload), qos=0)
        time.sleep(2)
except KeyboardInterrupt:
    pass
finally:
    client.loop_stop()
    client.disconnect()
