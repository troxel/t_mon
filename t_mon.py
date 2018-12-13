#!/usr/bin/python3

# Import Libraries
import os
import glob
import time
import re
import pprint
import collections
import datetime
import json
import sys

# Local module with common file specifications
import fspec

# Check for another session running and kill it
import solo
solo.chk_and_stopall(__file__)

# Disk utils to facilitate rw/ro ops
from commonutils import Utils
utils = Utils()

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run with no stdout",action="store_true")
args = parser.parse_args()

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm') # Turns on the temperature module

# ------- GPIO stuff -----------
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
# ------------------------------

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
dev_file_lst = list( map( lambda x: x+'/w1_slave' , glob.glob(base_dir +  '28*') ) )

if not dev_file_lst:
   print("No temperature devices found\n")
   exit(1)

# Set up device list
dev_hsh = {}
flot_lst = []
for dev_file in dev_file_lst:
   rtn = re.search("28-(\w+)",dev_file)
   dev_id = rtn.group(1)
   dq = collections.deque(maxlen=70) # circ buffer
   dev_hsh[dev_file] = { "dev_id":dev_id, "bufr":dq, "trip_cnt":0, "dev_file":dev_file }

   flot_lst.append({ "label":dev_id, "data":[]} )

   #plot_data = [ { label: "Foo", data: [ [10, 1], [17, -14], [30, 5] ] },
   #{ label: "Bar", data: [ [11, 13], [19, 11], [30, -7] ] } ]

# --------- util functions ---------------------
def read_temp(dev_file):
  rd_attempts = 5

  # After so many attempts error and move on
  for x in range(rd_attempts):

      f = open(dev_file, 'r')
      lines = f.readlines()
      f.close()

      # Coded message looks like
      # 67 01 55 00 7f ff 0c 10 f9 : crc=f9 YES
      if re.search("YES$",lines[0]):
        rtn = re.search('t=(\d+)',lines[1])
        temp_c = float(rtn.group(1)) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_f

      time.sleep(0.5)

  raise Exception('Cannot get a good read')
  return False

# If triggered call back module is present and defined use it.
# Using a triggered module allows us to generalized the code and use
# customized responses.
try:
   from triggered import triggered
except ImportError:
   # If not just used a dummy
   def triggered():
      print("triggered locally")

# ----------------------------------------------------------------------
# Start...
# ----------------------------------------------------------------------
print("Starting")

# -- Configuration parameters --
#temp_f_max = 77 # Trigging Temperature
#trip_max   = 3  # Number of times to exceed temp_f_max before triggering
#cycle_time = 5  # Number of seconds per sampling

# Move to file so that t_web can gain access...
from threshold import temp_f_max,trip_max,cycle_time

# --- GPIO ------
pin_status = 31
GPIO.setup( pin_status, GPIO.OUT)

pin_ac = 33
GPIO.setup( pin_ac , GPIO.OUT)

pin_vsense = 29
GPIO.setup( pin_vsense , GPIO.IN)

# GPIO ISR
def vsense(channel):
   # A/C indicator
   if GPIO.input(pin_vsense):
      GPIO.output(pin_ac, True)
   else:
      GPIO.output(pin_ac, False)

GPIO.add_event_detect(pin_vsense, GPIO.BOTH, callback=vsense)

vsense(pin_vsense)

# --------------------------
while(1):

   t_last = []
   time_rec = int(time.time()) * 1000;
   inx = 0
   for dev_file in list( dev_hsh.keys() ):

      try:
         temp_f = read_temp(dev_file)
      except Exception as err:
         print("Exception {0} at {1}".format(err,time_str))
         time.sleep(2)
         next

      # plotting to do plotting
      dev_hsh[dev_file]['bufr'].append([ time_rec, temp_f ])

      flot_lst[inx]["data"] = list(dev_hsh[dev_file]['bufr']
      )
      inx = inx + 1

      time_str = str( datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
      msg = "{} {} {:.1f}".format(time_str,dev_hsh[dev_file]['dev_id'],temp_f)
      if not args.q: print(msg)

      t_last.append( {'time_str':time_str, 'dev_id':dev_hsh[dev_file]['dev_id'], 'temp_f':"{:.1f}".format(temp_f)} )

      # Check if limit exceeded
      if temp_f > temp_f_max:
         dev_hsh[dev_file]['trip_cnt'] = dev_hsh[dev_file]['trip_cnt'] + 1
         print("Device {} is over max at {:.1f} cnt is {}".format(dev_hsh[dev_file]['dev_id'],temp_f,dev_hsh[dev_file]['trip_cnt']))
      else:
         dev_hsh[dev_file]['trip_cnt'] = 0

      # Send power down if trip_max times in a row
      if dev_hsh[dev_file]['trip_cnt'] > trip_max:

         triggered()

         msg = "{} {} POWER GOING Down Temperature is {:.1f}\n".format(time_str,dev_id,temp_f)

         utils.rw()
         fd = open(fspec.pwr_down_log,'a')
         fd.write(msg)
         fd.close()
         utils.ro()

         dev_hsh[dev_file]['trip_cnt'] = 0

   utils.write_sysfile(fspec.t_last, json.dumps(t_last))
   utils.write_sysfile(fspec.state_json,json.dumps(flot_lst))

   # Set LEDs
   for inx in range(cycle_time):
      if GPIO.input(pin_status):
            GPIO.output(pin_status,False)
      else:
            GPIO.output(pin_status,True)
      time.sleep(1)
