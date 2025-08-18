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

# event handler for MQTT messages
def mqtt_MyTestTopic_event(data):
  global mqtt_client, wlan
  print(data[0]) # topic
  print(data[1]) # payloadz

def setup():
  global base_tfcard, gpsv11_0, time,label0, label1, label2,status,curr_velocity_knots,INIT,RUNNING,PAUSE,GPS_READY,gps_log_object,gps_data_list,file_exists,mqtt_client,wlan,use_mqtt

  # Initialize M5Stack
  M5.begin()
  Widgets.fillScreen(0x000000) # black background

  wlan = network.WLAN(network.STA_IF) # Station mode
  wlan.disconnect() # Disconnect if already connected
  
  while wlan.isconnected(): # Ensure we are disconnected
    pass
  
  
  wlan.connect('0xbeefbeef', '0xdeaddead') # Replace with your Wi-Fi credentials
  
  use_mqtt = True # Set to True to use MQTT, False to skip MQTT setup
  

  while not (wlan.isconnected()): # Wait for Wi-Fi connection
    pass


  mqtt_client = MQTTClient('MousetrapCar', '192.168.86.250', port=1883, user='', password='', keepalive=300) # Replace with your MQTT broker details
  if not mqtt_client == 0: # Check if MQTT client is created successfully
    print ('mqtt client session created')
  mqtt_client.connect(clean_session=True)# Connect to the MQTT broker
  mqtt_client.subscribe('CarVelocity_Q0', mqtt_MyTestTopic_event, qos=0)# Subscribe to the topic

  gpsv11_0 = GPSV11Unit(2, port=(1, 2))# Initialize GPS unit on port 2
  gpsv11_0.set_work_mode(7)# Set GPS work mode to 7 (NMEA + GPRMC)
  gpsv11_0.set_time_zone(2)# Set time zone to UTC+2
  
  base_tfcard = AtomicTFCardBase(slot=3, width=1, sck=7, miso=8, mosi=6, freq=1000000) # Initialize TF card base on slot 3  
  print(os.listdir('/sd/'))#  List files in the root directory of the TF card

  
  label0 = Widgets.Label(str(INIT_MESSAGE), 3, 40, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu12) # Initialize label for displaying GPS data
  label1 = Widgets.Label("Reset", 3, 85, 1.0, 0xdadada, 0x333333, Widgets.FONTS.DejaVu18) # Initialize label for reset button
  label2 = Widgets.Label("Start", 73, 85, 1.0, 0x3acb5c, 0x082a11, Widgets.FONTS.DejaVu18) # Initialize label for start/stop button
  
  mqtt_client.publish('CarVelocity_Q0', 'SetupComplete', qos=0) # Publish a message indicating setup is complete

  status = 0 # Initialize status variable
  velocity = 0 # Initialize velocity variable
  file_exists = False # Flag to check if the log file exists
  INIT = 0 
  RUNNING = 1
  PAUSE = 2

def loop():
  global base_tfcard, gpsv11_0, time, label0, label1,label2,status,INIT,RUNNING,PAUSE,curr_velocity_knots,curr_GPS_state,gps_data_list,file_exists,mqtt_client,wlan,INIT_MESSAGE

  M5.update() # Update M5Stack state
  mqtt_client.check_msg() # Check for incoming MQTT messages
    
  if BtnA.wasClicked(): # Button A clicked
    if status == INIT: # Initial state
      curr_GPS_state=gpsv11_0.get_speed_over_ground() # Get current GPS state
      if curr_GPS_state == '0': # If GPS is not ready
          label0.setText(str('                                ')) #Clear label0
          label0.setText(str('WAIT: GPS NOT READY')) #  Display waiting message
          time.sleep_ms(1000) # Wait for 1 second
          label0.setText(str(INIT_MESSAGE)) # Reset label0 to initial message         
      else:
          status = RUNNING
          velocity = gpsv11_0.get_gps_time() # Get current GPS time
          label0.setText(str('                                ')) # Clear label0
          label0 = Widgets.Label(str(velocity), 35, 40, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu18) # Update label0 with current velocity
          label2.setColor(0xe6463b, 0x310e0a) # Change label2 color to indicate running state
          label2.setText(str('stop')) # Update label2 text to 'stop'
    elif status == RUNNING: # Running state
      status = PAUSE # Change status to pause
      if len(gps_data_list) > 0: #    If there are GPS data points to save
          label0.setText(str('                                '))# Clear label0
          label0.setText(str('SAVING DATA'))# Display saving data message
          time.sleep_ms(100)# Wait for 100 milliseconds
          #os.chdir("/sd/drfizzix/")
          file_exists = False # Flag to check if the log file exists
          for item in os.listdir('/sd/drfizzix'): # List files in the /sd/drfizzix directory
            if item == 'location_log.csv': # Check if the log file exists
                file_exists = True # Set flag to True if file exists
                print('existing file in drfizzix')    
                break
            
          with open('/sd/drfizzix/location_log.csv', 'a') as f: # Open the log file in append mode
              if not file_exists: 
                # If the file is new, write the header first
                header = "timestamp,latitude,longitude\n" # Define the header for the CSV file
                print('about to write data') 
                f.write(header) # Write the header to the file
                print('Created new log file and wrote header: /sd/drfizzix/location_log.csv')
           
              # Write the actual data log
              print('about to write data')
              
              for item in gps_data_list: # Iterate through the GPS data list
                  f.write(str(item)+'\n') # Write each item to the file
              gps_data_list.clear() # Clear the GPS data list after writing to the file
              
              print("Successfully appended {bytes_written} bytes to /sd/drfizzix/location_log.csv")
              f.close() # Close the file after writing
              label0.setText(str('                                ')) # Clear label0
              label0.setText(str('DATA SAVED'))# Display data saved message
              time.sleep_ms(1000)
              label0.setText(str('                                '))
              label0.setText(str(INIT_MESSAGE)) # Reset label0 to initial message
                       
                
      label2.setColor(0x3acb5c, 0x082a11) # Change label2 color to indicate pause state
      label2.setText(str('start')) # Update label2 text to 'start'
    elif status == PAUSE: # Pause state
      status = RUNNING #  Change status to running 
      velocity = gpsv11_0.get_gps_time()# Get current GPS time
      last_velocity = velocity # Store last velocity
      label2.setColor(0xe6463b, 0x3e0e0a) # Change label2 color to indicate running state
      label2.setText(str('stop')) # Update label2 text to 'stop'
  if BtnA.wasDoubleClicked():
    status = INIT # Reset status to initial state
    gps_data_list.clear()
    
    count_ms = 0
    label0.setText(str(INIT_MESSAGE)) # Reset label0 to initial message
    label2.setColor(0x3acb5c, 0x082a11) # Change label2 color to indicate initial state
    label2.setText(str('start')) # Update label2 text to 'start'
    last_velocity = 0     
  if status == RUNNING:
    curr_time = gpsv11_0.get_gps_time() # Get current GPS time
    curr_longitude = gpsv11_0.get_longitude() # Get current GPS longitude
    curr_latitude = gpsv11_0.get_latitude()   # Get current GPS latitude
    curr_velocity_knots = gpsv11_0.get_speed_over_ground()  # Get current GPS speed in knots
    velocity_str= str(curr_velocity_knots) # Convert current velocity to string 
    velocity_time_str=str(velocity_str + ' ' + str(curr_time)) # Combine velocity and time into a string
    
    velocity_meters_str=str(curr_velocity_knots) + ' m/s' # Convert current velocity to meters per second string; todo: need to do math to convert knots to m/s
    label0.setText(str(velocity_str)) # Update label0 with current velocity
    mqtt_client.publish('CarVelocity_Q0', str(velocity_time_str), qos=0)  # Publish current velocity and time to MQTT topic

    gps_data_list.append({
        "time": curr_time,
        "latitude": curr_latitude,
        "longitude": curr_longitude,
        "velocity_knots": curr_velocity_knots
    })      # Append current GPS data to the list 
  time.sleep_ms(100)    # Sleep for 100 milliseconds to avoid busy-waiting

if __name__ == '__main__':
  try:
    setup()     # Call setup function to initialize everything         
    while True:
      loop()                                      # Call loop function to continuously check for button presses and update GPS data
  except (Exception, KeyboardInterrupt) as e:         # Catch any exceptions or keyboard interrupts
    try:
      from utility import print_error_msg             # Import utility function to print error messages
      print_error_msg(e)                                          
    except ImportError:
      print("please update to latest firmware")

