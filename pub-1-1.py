import paho.mqtt.client as mqtt
import time
from datetime import datetime
import random


# create an instance of MQTT broker 
mqttBroker="broker.hivemq.com" 
port = 1883

#topics to publish to
temperature_topic="cnc1/sensor/temperature"

# Callback when connected
def on_connect(client, userdata, flags, rc, properties):
    if rc==0:
        print (f"connected to broker with code {rc}")
        
    else:
        print("not connected")     

# Callback when broker ACKs a publish
def on_publish(client, userdata, mid, reason_codes, properties):
    print(f"? Broker ACKed publish with message ID: {mid} , {reason_codes}")


#create client instance and connect to the broker on port 1883
client=mqtt.Client (client_id="CNC1", callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.connect(mqttBroker,port)



client.on_connect=on_connect
client.on_publish = on_publish

client.loop_start()  # Starts a background thread to handle network traffic. The Paho MQTT client needs a loop running in the background


#publish temperature data every 2 seconds

while True:

    now=datetime.now()
    temperature = round(random.uniform(20.0, 30.0), 2)  # Simulated 

    info=client.publish(temperature_topic,temperature, qos=0)
    time.sleep(5)


    print(f"Published: {temperature} °C to topic {temperature_topic} at {now}, message ID={info.mid} ")
