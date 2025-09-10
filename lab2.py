from machine import Pin
import dht, time

# DHT22 data pin connected to pin 15 (change if needed)
sensor = dht.DHT22(Pin(15))

print("DHT22 plot: temp °C and hum %")

while True:
    try:
        sensor.measure()
        t = sensor.temperature()   # °C
        h = sensor.humidity()      # %
        # Two series on one line → Wokwi Serial Plotter shows two curves
        print("temp:{:.2f}\thum:{:.2f}".format(t, h))
    except OSError:
        # Plot gaps if a read fails
        print("temp:NaN\thum:NaN")
    time.sleep(2)  # sample every 2 seconds
