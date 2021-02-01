
'''
>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
Project name    :   The Gardener
Description     :   Reads moisture and controls water pump
@bencarpena     :   20201011 : 	initial release
				:	20201017 :	added furion protocols and enhancements
				:	20201017 :	troubleshoot and deploy
				:	20201023 : 	added soil saturation notice subroutine
				:	20201219 :	Added MQTT and Azure IoT Hub integration
				:	20201221 :	Lengthen hydration duration from 4.25 to 4.65
				:	20201221 :	Set watering threshold to 18000 from 17009
				:	20201222 :	Added sys args to make hydration threshold an input parameter
				:	20201226 :	Reformatted JSON payload to IoT Hub

Credits:

#SwitchDoc Labs May 2016
# reads all four channels from the Grove4Ch16BitADC Board in single ended mode
# also reads raw values
#

# MQTT personal notes:
https://onedrive.live.com/view.aspx?resid=BE42616FC86F2AB8%2119663&id=documents&wd=target%28IoT.one%7C2C2A8BC3-E1B8-2541-9366-F6F8E984C1BF%2FIntegrating%20MQTT%20and%20Azure%20IoT%20Hub%7CCB2F4618-D393-034D-95F5-04A5DFAE8239%2F%29

>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''


import time, signal, sys

from time import sleep
from datetime import datetime

import SDL_Adafruit_ADS1x15 
import os, ssl
import requests
import json


import RPi.GPIO as GPIO

from paho.mqtt import client as mqtt
import sys



if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): 
			ssl._create_default_https_context = ssl._create_unverified_context

sensor_args = { 'ch0': 'Accepting variable input',
                'sysdf': 'Use pre-defined limit'
                }
if len(sys.argv) == 3 and sys.argv[1] in sensor_args:
	print(sys.argv[0])
	print(sys.argv[1])
	print(sys.argv[2])
	if sys.argv[1] == 'sysdf':
		_sensor_threshold = 18000
	else:
		_sensor_threshold = int(sys.argv[2])

else:
    print('Usage: sudo ./thegardener.py [ch0|sysdf] <threshold value integer>')
    print('Example: sudo ./thegardener.py ch0 18000 (where 18000 is the soil saturation limit and will cause pumps to turn on)')
    sys.exit(1)

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
webhook_url = 'https://hooks.slack.com/services/(creds-here)'


#   Setup GPIO
signal_pin = 4
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(signal_pin, GPIO.OUT)


def start_hydrate_furion():
    GPIO.output(signal_pin, GPIO.LOW)
    print ("[INFO] : Watering Furion now!") #turn on water pump
    time.sleep(4.65)

def stop_hydrate_furion():
    GPIO.output(signal_pin, GPIO.HIGH) #turn off water pump
    print ("[INFO] : Watering Furion stopped!") 
    time.sleep(1)

def clean_up_subroutine():
	GPIO.output(signal_pin, GPIO.HIGH) #turn off water pump
	print ("[INFO] : Shutting down water pumps") 

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
	slack_msg = {'text' : 'alphard (the_gardener) | ' + str(dtstamp) + " | _Ch0_Param = " + str(_sensor_threshold) + " Channel 0 =%.6fV raw=0x%4X dec=%d" % (voltsCh0, rawCh0, rawCh0)}
	slack_msg_mqtt = '{"iot_msg_from" : "alphard(iot/g01)", "iot_dt" : "' + str(dtstamp) + '", "iot_rd" : "Ch0_Param = ' + str(_sensor_threshold) + " | Channel 0 =%.6fV raw=0x%4X dec=%d" % (voltsCh0, rawCh0, rawCh0) + '"}'


	# @bencarpena 20201013 : Added post to Slack (alphard-iot channel)
	requests.post(webhook_url, data=json.dumps(slack_msg))
	print ("Success : Posted data to Slack!")


	# @bencarpena 20201219 : Send message to IoT Hub via MQTT
	# START : MQTT < #############################
	path_to_root_cert = "/certs/Baltimore.pem"
	device_id = "alphard02"
	sas_token = "SharedAccessSignature (token here)"
	iot_hub_name = "alphard_iot_hub"


	def on_connect(client, userdata, flags, rc):
		print("alphard (mode: iot/g01) connected with result code: " + str(rc))


	def on_disconnect(client, userdata, rc):
		print("alphard (mode: iot/g01) disconnected with result code: " + str(rc))


	def on_publish(client, userdata, mid):
		print("alphard (mode: iot/g01) sent message!")
		print("JSON payload sent: ", slack_msg_mqtt)

	def on_message(client, userdata, message):
		print("message received " ,str(message.payload.decode("utf-8")))
		print("message topic=",message.topic)
		print("message qos=",message.qos)
		print("message retain flag=",message.retain)

	def on_log(client, userdata, level, buf):
		print("log: ",buf)


	client = mqtt.Client(client_id=device_id, protocol=mqtt.MQTTv311)
	client.on_message=on_message 
	client.on_connect = on_connect
	client.on_disconnect = on_disconnect
	client.on_publish = on_publish

	client.username_pw_set(username=iot_hub_name+".azure-devices.net/" +
						device_id + "/?api-version=2018-06-30", password=sas_token)

	client.tls_set(ca_certs=path_to_root_cert, certfile=None, keyfile=None,
				cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
	client.tls_insecure_set(False)

	client.connect(iot_hub_name+".azure-devices.net", port=8883)

	#start the loop
	client.loop_start() 

	#subscribe to topic
	client.subscribe("devices/" + device_id + "/messages/events/")

	#publish message
	client.publish("devices/" + device_id + "/messages/events/", slack_msg_mqtt, qos=1) 

	#give time to process subroutines
	sleep(5)

	#display log
	client.on_log=on_log


	#end the loop
	client.loop_stop()

	# END MQTT > #############################

	#processing data and sensor readings -------------
	#20201222 : Updated : if int(sensor_readings[-1]) > 18000: 
	if int(sensor_readings[-1]) > _sensor_threshold:
		start_hydrate_furion()
		stop_hydrate_furion()
		dtstamp = datetime.now()
		slack_msg = {'text' : 'alphard (the_gardener) | ' + str(dtstamp) + " | Furion protocol initiated!"}
		requests.post(webhook_url, data=json.dumps(slack_msg))
		print ("Success : Furion Hydration Protocol invoked!")

	if int(sensor_readings[-1]) < 10000:
		slack_msg = {'text' : 'alphard (the_gardener) | ' + str(dtstamp) + " | Soil is saturated {dec_code: " + str(sensor_readings[-1]) + ", voltage: " + str(voltsCh0) + "}. Sunlight required! "}
		requests.post(webhook_url, data=json.dumps(slack_msg))
		print ("INFO : Soil is saturated!")



except:
	#clean_up_subroutine()
	slack_msg = {'text' : 'alphard (the_gardener | iot/g01) : Exception occurred! ' + str(datetime.now())}
	requests.post(webhook_url, data=json.dumps(slack_msg))
	
	#Catch and display exception
	_exception = sys.exc_info()[0]
	print(_exception)

	os.execv(__file__, sys.argv) # Heal process and restart
finally:
   print("System " + str(datetime.now()) + " : Cleaning up GPIOs.") 
   clean_up_subroutine()
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
