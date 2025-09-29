# this code is related to HW 04 - MQTT QoS Comparision
import time
import paho.mqtt.client as mqtt

BROKER = "broker.hivemq.com"
PORT   = 1883
TOPIC  = "msn-asu/qos-demo/ack"

def on_connect(client, userdata, flags, rc):
    print("Connected rc=", rc)

def on_publish(client, userdata, mid):
    t0 = userdata["t_send"].pop(mid, None)
    if t0:
        rtt = (time.time() - t0) * 1000
        print(f"on_publish: mid={mid} finished (QoS {userdata['qos']}) rtt≈{rtt:.1f} ms")
    else:
        print(f"on_publish: mid={mid}")

def on_log(client, userdata, level, buf):
    # Show just the publish/ack handshake with the broker
    if any(k in buf for k in ("PUBLISH", "PUBACK", "PUBREC", "PUBREL", "PUBCOMP")):
        print("LOG:", buf)

# --- ask for QoS once ---
while True:
    try:
        qos = int(input("Enter QoS (0, 1, or 2): ").strip())
        if qos in (0, 1, 2):
            break
    except ValueError:
        pass
    print("Please enter 0, 1, or 2.")

userdata = {"t_send": {}, "qos": qos}

client = mqtt.Client(client_id="qos-pub-demo", clean_session=True, userdata=userdata)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_log = on_log

client.connect(BROKER, PORT, keepalive=30)
client.loop_start()

i = 0
try:
    print(f"Publishing to {TOPIC} with QoS {qos}. Press Ctrl+C to stop.")
    while True:
        i += 1
        payload = f"msg {i} (QoS={qos})"
        rc, mid = client.publish(TOPIC, payload, qos=qos, retain=False)
        userdata["t_send"][mid] = time.time()
        print(f"SEND: mid={mid} -> {payload}")
        time.sleep(1.5)
except KeyboardInterrupt:
    print("\nStopping...")
finally:
    client.loop_stop()
    client.disconnect()
