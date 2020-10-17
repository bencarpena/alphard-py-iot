import time

import RPi.GPIO as GPIO

#   Setup GPIO
signal_pin = 4
GPIO.setmode(GPIO.BCM) # Broadcom pin-numbering scheme
GPIO.setup(signal_pin, GPIO.OUT)




def start_hydrate_furion():
    GPIO.output(signal_pin, GPIO.LOW)
    print ("[INFO] : Watering Furion now!") #turn on water pump
    time.sleep(1.5)


def stop_hydrate_furion():
    GPIO.output(signal_pin, GPIO.HIGH) #turn off water pump
    print ("[INFO] : Watering Furion stopped!") 
    time.sleep(1)




if __name__ == '__main__':
    try:
        start_hydrate_furion()
        stop_hydrate_furion()
        GPIO.cleanup()
    except KeyboardInterrupt:
        GPIO.cleanup()