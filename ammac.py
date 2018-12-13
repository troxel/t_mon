#!/usr/bin/python3

# requirements
#"amac alpha_supply off"
#"amac beta_supply off"

# ------- GPIO stuff -----------
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

pin_alpha = 38;
GPIO.setup( pin_alpha, GPIO.OUT)

pin_beta  = 40;
GPIO.setup( pin_beta, GPIO.OUT)
# ------------------------------

import sys
import os

def synopsis():

   print("Synopsis:")
   print("amac alpha_supply on\namac beta_supply on")
   print("amac alpha_supply off\namac beta_supply off\n\n")
   sys.exit(1)

if len( sys.argv ) != 3:
   synopsis()

cmd = sys.argv[1]
onoff = sys.argv[2]

if onoff == "on":
   onoff_cmd = True
elif onoff == "off":
   onoff_cmd = False
else:
   synopsis()

if cmd == "alpha_supply":
   pin_cmd = pin_alpha
elif cmd == "beta_supply":
   pin_cmd = pin_beta

GPIO.output(pin_cmd,onoff_cmd)
