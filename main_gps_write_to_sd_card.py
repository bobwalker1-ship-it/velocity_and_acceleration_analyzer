import os, sys, io
import M5
from M5 import *
from unit import GPSV11Unit
from base import AtomicTFCardBase
import time
from umqtt import *
import network

mqtt_client = None
wlan = None

base_tfcard = None
gpsv11_0 = None
gps_log_object = None


# 1. Using a List of Dictionaries
# This is a very common and flexible method. Each item in the list is a
# dictionary representing a single point-in-time reading.
gps_data_list = []
MOUNT_POINT = '/sd/drfizzix/'
LOG_FILE = 'location_log.csv'
INIT_MESSAGE = 'Approaching Zero'

def mqtt_MyTestTopic_event(data):
  global mqtt_client, wlan
  print(data[0])
  print(data[1])

def setup():
  global base_tfcard, gpsv11_0, time,label0, label1, label2,status,curr_velocity_knots,INIT,RUNNING,PAUSE,GPS_READY,gps_log_object,gps_data_list,file_exists,mqtt_client,wlan,use_mqtt


  M5.begin()
  Widgets.fillScreen(0x000000)

  wlan = network.WLAN(network.STA_IF)
  wlan.disconnect()
  
  while wlan.isconnected():
    pass
  
  
  wlan.connect('0xbeefbeef', '0xdeaddead')
  
  use_mqtt = True
  

  while not (wlan.isconnected()):
    pass


  mqtt_client = MQTTClient('MousetrapCar', '192.168.86.250', port=1883, user='', password='', keepalive=300)
  if not mqtt_client == 0:
    print ('mqtt client session created')
  mqtt_client.connect(clean_session=True)
  mqtt_client.subscribe('CarVelocity_Q0', mqtt_MyTestTopic_event, qos=0)

  gpsv11_0 = GPSV11Unit(2, port=(1, 2))
  gpsv11_0.set_work_mode(7)
  gpsv11_0.set_time_zone(2)
  
  base_tfcard = AtomicTFCardBase(slot=3, width=1, sck=7, miso=8, mosi=6, freq=1000000)
  print(os.listdir('/sd/'))

  
  label0 = Widgets.Label(str(INIT_MESSAGE), 3, 40, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu12)
  label1 = Widgets.Label("Reset", 3, 85, 1.0, 0xdadada, 0x333333, Widgets.FONTS.DejaVu18)
  label2 = Widgets.Label("Start", 73, 85, 1.0, 0x3acb5c, 0x082a11, Widgets.FONTS.DejaVu18)
  
  mqtt_client.publish('CarVelocity_Q0', 'SetupComplete', qos=0)

  status = 0
  velocity = 0
  file_exists = False
  INIT = 0
  RUNNING = 1
  PAUSE = 2

def loop():
  global base_tfcard, gpsv11_0, time, label0, label1,label2,status,INIT,RUNNING,PAUSE,curr_velocity_knots,curr_GPS_state,gps_data_list,file_exists,mqtt_client,wlan,INIT_MESSAGE

  M5.update()
  mqtt_client.check_msg()
    
  if BtnA.wasClicked():
    if status == INIT:
      curr_GPS_state=gpsv11_0.get_speed_over_ground()
      if curr_GPS_state == '0':
          label0.setText(str('                                '))
          label0.setText(str('WAIT: GPS NOT READY'))
          time.sleep_ms(1000)
          label0.setText(str(INIT_MESSAGE))          
      else:
          status = RUNNING
          velocity = gpsv11_0.get_gps_time()
          label0.setText(str('                                '))
          label0 = Widgets.Label(str(velocity), 35, 40, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu18)
          label2.setColor(0xe6463b, 0x310e0a)
          label2.setText(str('stop'))
    elif status == RUNNING:
      status = PAUSE
      if len(gps_data_list) > 0:
          label0.setText(str('                                '))
          label0.setText(str('SAVING DATA'))
          time.sleep_ms(100)
          #os.chdir("/sd/drfizzix/")
          file_exists = False
          for item in os.listdir('/sd/drfizzix'):
            if item == 'location_log.csv':
                file_exists = True
                print('existing file in drfizzix')
                break
            
          with open('/sd/drfizzix/location_log.csv', 'a') as f:
              if not file_exists:
                # If the file is new, write the header first
                header = "timestamp,latitude,longitude\n"
                print('about to write data')
                f.write(header)
                print('Created new log file and wrote header: /sd/drfizzix/location_log.csv')
           
              # Write the actual data log
              print('about to write data')
              
              for item in gps_data_list:
                  f.write(str(item)+'\n')
              
              print("Successfully appended {bytes_written} bytes to /sd/drfizzix/location_log.csv")
              f.close()
              label0.setText(str('                                '))
              label0.setText(str('DATA SAVED'))
              time.sleep_ms(1000)
              label0.setText(str('                                '))
              label0.setText(str(INIT_MESSAGE))
              
      

          
      label2.setColor(0x3acb5c, 0x082a11)
      label2.setText(str('start'))
    elif status == PAUSE:
      status = RUNNING
      velocity = gpsv11_0.get_gps_time()
      last_velocity = velocity
      label2.setColor(0xe6463b, 0x3e0e0a)
      label2.setText(str('stop'))
  if BtnA.wasDoubleClicked():
    status = INIT
    count_ms = 0
    label0.setText(str(INIT_MESSAGE))
    label2.setColor(0x3acb5c, 0x082a11)
    label2.setText(str('start'))
    last_velocity = 0     
  if status == RUNNING:
    curr_time = gpsv11_0.get_gps_time()
    curr_longitude = gpsv11_0.get_longitude()
    curr_latitude = gpsv11_0.get_latitude()
    curr_velocity_knots = gpsv11_0.get_speed_over_ground()
    velocity_str= str(curr_velocity_knots)
    velocity_time_str=str(velocity_str + ' ' + str(curr_time))
    
    velocity_meters_str=str(curr_velocity_knots) + ' m/s'
    label0.setText(str(velocity_str))
    mqtt_client.publish('CarVelocity_Q0', str(velocity_time_str), qos=0)

    # Method 3: Create an instance of the GpsReading class and add it to our log
    # Method 1: Append a new dictionary to the list
    gps_data_list.append({
        "time": curr_time,
        "latitude": curr_latitude,
        "longitude": curr_longitude,
        "velocity_knots": curr_velocity_knots
    })
  time.sleep_ms(100)

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

