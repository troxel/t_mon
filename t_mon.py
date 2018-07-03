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

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run with no stdout",action="store_true")
args = parser.parse_args()

# Initialize the GPIO Pins
os.system('modprobe w1-gpio')  # Turns on the GPIO module
os.system('modprobe w1-therm') # Turns on the temperature module

# Finds the correct device file that holds the temperature data
base_dir = '/sys/bus/w1/devices/'
dev_file_lst = list( map( lambda x: x+'/w1_slave' , glob.glob(base_dir +  '28*') ) )

if not dev_file_lst:
   print("No temperature devices found\n")
   exit(1)

# Set up device list
dev_hsh = {}
for dev_file in dev_file_lst:
   rtn = re.search("28-(\w+)",dev_file)
   dev_id = rtn.group(1)
   dq = collections.deque(maxlen=10) # circ buffer
   dev_hsh[dev_file] = { "dev_id":dev_id, "bufr":dq, "trip_cnt":0, "dev_file":dev_file }

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
temp_f_max = 77 # Trigging Temperature
trip_max = 3    # Number of times to exceed temp_f_max before triggering
cycle_time = 5  # Number of seconds per sampling
# --------------------------
while(1):

   t_last = []
   for dev_file in list( dev_hsh.keys() ):

      try:
         temp_f = read_temp(dev_file)
      except Exception as err:
         print("Exception {0} at {1}".format(err,time_str))
         time.sleep(2)
         next

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

      # Send power down if trim_max times in a row
      if dev_hsh[dev_file]['trip_cnt'] > trip_max:

         triggered()
         msg = "{} {} POWER GOING Down Temperature is {:.1f}\n".format(time_str,dev_id,temp_f)
         print(msg)
         fd = open(fspec.pwr_down_log,'a')
         fd.write(msg)
         fd.close()

         dev_hsh[dev_file]['trip_cnt'] = 0


   fd = open(fspec.t_last,'w')
   fd.write(json.dumps(t_last))
   fd.close()

   time.sleep(5)
