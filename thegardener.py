
'''
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Project name    :   The Gardener
Description     :   Reads moisture and controls water pump
@bencarpena     :   20201011 : 	initial release
				:	20201017 :	added furion protocols and enhancements

Credits:

#SwitchDoc Labs May 2016
#
# reads all four channels from the Grove4Ch16BitADC Board in single ended mode
# also reads raw values
#

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''


import time, signal, sys
sys.path.append('./SDL_Adafruit_ADS1x15')

from time import sleep
from datetime import datetime

import SDL_Adafruit_ADS1x15 
import os, ssl
import requests
import json


import RPi.GPIO as GPIO


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): 
			ssl._create_default_https_context = ssl._create_unverified_context


def signal_handler(signal, frame):
        print( 'You pressed Ctrl+C!')
        sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

ADS1115 = 0x01	# 16-bit ADC

# Select the gain
# gain = 6144  # +/- 6.144V
gain = 4096  # +/- 4.096V
# gain = 2048  # +/- 2.048V
# gain = 1024  # +/- 1.024V
# gain = 512   # +/- 0.512V
# gain = 256   # +/- 0.256V

# Select the sample rate
# sps = 8    # 8 samples per second
# sps = 16   # 16 samples per second
# sps = 32   # 32 samples per second
# sps = 64   # 64 samples per second
# sps = 128  # 128 samples per second
sps = 250  # 250 samples per second
# sps = 475  # 475 samples per second
# sps = 860  # 860 samples per second

# Initialise the ADC using the default mode (use default I2C address)
adc = SDL_Adafruit_ADS1x15.ADS1x15(ic=ADS1115)

# Initialize slack webhook
webhook_url = '===your Slack Webhook here==='


#   Setup GPIO
signal_pin = 4
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(signal_pin, GPIO.OUT)


def start_hydrate_furion():
    GPIO.output(4, GPIO.LOW)
    print ("[INFO] : Watering Furion now!") #turn on water pump
    time.sleep(3.75)

def stop_hydrate_furion():
    GPIO.output(signal_pin, GPIO.HIGH) #turn off water pump
    print ("[INFO] : Watering Furion stopped!") 
    time.sleep(1)

def failsafe():
	GPIO.output(signal_pin, GPIO.HIGH) #turn off water pump
	slack_msg = {'text' : 'alphard (the_gardener) : Exception occurred! ' + str(datetime.datetime.now())}
	requests.post(webhook_url, data=json.dumps(slack_msg))
	GPIO.cleanup()

try:
	#main subroutines
	print ("START gardener reading ###################\n")
	voltsCh0 = adc.readADCSingleEnded(0, gain, sps) / 1000
	rawCh0 = adc.readRaw(0, gain, sps) 
	
	#store sensor readings ---------
	sensor_readings = []
	sensor_readings.append (str(voltsCh0))
	sensor_readings.append(str(rawCh0))
	print (str(sensor_readings[:]))
	
	print ("\nChannel 0 =%.6fV raw=0x%4X dec=%d" % (voltsCh0, rawCh0, rawCh0))
	print ("END gardener reading ###################")

	dtstamp = datetime.now()
	slack_msg = {'text' : 'alphard (the_gardener) | ' + str(dtstamp) + " | Channel 0 =%.6fV raw=0x%4X dec=%d" % (voltsCh0, rawCh0, rawCh0)}

	# @bencarpena 20201013 : Added post to Slack (alphard-iot channel)
	requests.post(webhook_url, data=json.dumps(slack_msg))
	print ("Success : Posted data to Slack!")

	#processing data and sensor readings -------------
	if int(sensor_readings[-1]) > 17500:
		start_hydrate_furion()
		GPIO.cleanup()
		stop_hydrate_furion()
		GPIO.cleanup()
		dtstamp = datetime.now()
		slack_msg = {'text' : 'alphard (the_gardener) | ' + str(dtstamp) + " | Furion protocol initiated!"}
		requests.post(webhook_url, data=json.dumps(slack_msg))
		print ("Success : Furion Protocol invoked!")


except:
	failsafe()
	os.execv(__file__, sys.argv) # Heal process and restart
finally:
   print("System " + str(datetime.now()) + " : Cleaning up GPIOs. Furion protocols invoked.") 
   GPIO.cleanup() # cleanup all GPIO 

'''
======================================
Draft code for reading ADC outputs:
======================================
while (1):

	# Read channels  in single-ended mode using the settings above

	print ("--------------------")
	voltsCh0 = adc.readADCSingleEnded(0, gain, sps) / 1000
	rawCh0 = adc.readRaw(0, gain, sps) 
	print ("Channel 0 =%.6fV raw=0x%4X dec=%d" % (voltsCh0, rawCh0, rawCh0))
	voltsCh1 = adc.readADCSingleEnded(1, gain, sps) / 1000
	rawCh1 = adc.readRaw(1, gain, sps) 
	print ("Channel 1 =%.6fV raw=0x%4X dec=%d" % (voltsCh1, rawCh1, rawCh1))
	voltsCh2 = adc.readADCSingleEnded(2, gain, sps) / 1000
	rawCh2 = adc.readRaw(2, gain, sps) 
	print ("Channel 2 =%.6fV raw=0x%4X dec=%d" % (voltsCh2, rawCh2, rawCh2))
	voltsCh3 = adc.readADCSingleEnded(3, gain, sps) / 1000
	rawCh3 = adc.readRaw(3, gain, sps) 
	print ("Channel 3 =%.6fV raw=0x%4X dec=%d" % (voltsCh3, rawCh3, rawCh3))
	print ("--------------------")

	time.sleep(0.5)
'''