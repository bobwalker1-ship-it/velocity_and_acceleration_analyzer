import os, sys, io
import M5
from M5 import *
from umqtt import *
import network



mqtt_client = None
wlan = None


def btnA_wasReleased_event(state):
  global mqtt_client, wlan
  mqtt_client.publish('MyTestTopic', 'MyTestMsg', qos=0)


def mqtt_MyTestTopic_event(data):
  global mqtt_client, wlan
  print(data[0])
  print(data[1])


def setup():
  global mqtt_client, wlan

  M5.begin()
  Widgets.fillScreen(0x000000)

  BtnA.setCallback(type=BtnA.CB_TYPE.WAS_RELEASED, cb=btnA_wasReleased_event)

  wlan = network.WLAN(network.STA_IF)
  wlan.disconnect()
  while wlan.isconnected():
    pass
  wlan.connect('coolhandbob', 'Some1new599a')
  while not (wlan.isconnected()):
    pass
  mqtt_client = MQTTClient('MyTestClient', '192.168.86.20', port=1883, user='', password='', keepalive=300)
  if not mqtt_client == 0:
    print ('mqtt client session created')
  mqtt_client.connect(clean_session=True)
  mqtt_client.subscribe('MyTestTopic', mqtt_MyTestTopic_event, qos=0)
  mqtt_client.publish('MyTestTopic', 'MyTestMsg', qos=0)


def loop():
  global mqtt_client, wlan
  M5.update()
  mqtt_client.check_msg()


if __name__ == '__main__':
  try:
    setup()
    while True:
      loop()
  except (Exception, KeyboardInterrupt) as e:
    try:
      from utility import print_error_msg
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")
