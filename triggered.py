import os
import subprocess
import pprint

#data = {"user": "root",
#        "host": "10.10.80.201",
#        "password": "root",
#        "commands": ["amac alpha_supply off","amac alpha_suppply off"]}

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

pin_alpha = 38;
GPIO.setup( pin_alpha, GPIO.OUT)

pin_beta  = 40;
GPIO.setup( pin_beta, GPIO.OUT)

def triggered():

   GPIO.output(pin_alpha,False)
   GPIO.output(pin_beta,False)

   # Send email?

   return True



   # Old trigger function.... now we have combined the units.
   #command = "sshpass -p {password} ssh -q {user}@{host} {commands}".format(**data)
   #lst = command.split(' ')
   ###rtn = subprocess.run(lst, stdout=subprocess.PIPE)
   #pprint.pprint(lst)
   #print("rtn={}".format(rtn.stdout))
