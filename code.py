import board
import busio
import digitalio
from pms5003 import PMS5003
import time
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT

try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
    
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["password"])
print("Connected to %s!" % secrets["ssid"])

pm25_feed = secrets["aio_username"] + "/feeds/pm25"


### Code ###

# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    pass


def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from Adafruit IO!")


def message(client, topic, message):
    # This method is called when a topic the client is subscribed to
    # has a new message.
    print("New message on topic {0}: {1}".format(topic, message))


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

# Connect the client to the MQTT broker.
print("Connecting to Adafruit IO...")
mqtt_client.connect()

pm25_val = 0

uart = board.UART()

pms5003 = PMS5003(serial=uart,  pin_enable=board.IO7)

while True:
    data = pms5003.read()
    print("PM2.5 ug/m3 (combustion particles, organic compounds, metals): {}".format(data.pm_ug_per_m3(2.5)))
    print("PM1 ug/m3 (combustion particles, organic compounds, metals): {}".format(data.pm_ug_per_m3(1)))
    print("PM10 ug/m3 (combustion particles, organic compounds, metals): {}".format(data.pm_ug_per_m3(10)))
    mqtt_client.loop()
    
    pm25_val = data.pm_ug_per_m3(2.5)

    # Send a new message
    print("Sending pm25 value: %d..." % pm25_val)
    mqtt_client.publish(pm25_feed, pm25_val)
    print("Sent!")
    time.sleep(60)
