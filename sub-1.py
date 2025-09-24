import paho.mqtt.client as mqtt
import time



mqttBroker="broker.hivemq.com"
port = 1883

#topics to subscribe to
temperature_topic="cnc1/sensor/temperature"


def on_connect(client, userdata, flags, rc, properties): #callback function that gets executed every time the client is connected to the broker
    if rc==0:
        print (f"connected to broker with code {rc}")
        
    else:
        print("not connected")     

def on_messsage (client, udserdata, message):  # a callback function that gets executed every time a new message is received from a topic the client is subscribed to
    print(f" Receievd Topic:{message.topic}")
    print(" Temperature Value:" , message.payload.decode())  # decode payload to string

client = mqtt.Client(client_id="PC1", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect  # ✅ Attach callback BEFORE connecting
client.on_message = on_messsage # run on_message function whenever a subscribed message arrives


client.connect(mqttBroker, port)
client.subscribe(temperature_topic)




client.loop_start()
time.sleep(20) # Pauses the main thread for 20 seconds
client.loop_stop()








