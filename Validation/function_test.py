import datetime
import sqlite3
import subprocess
import time
import error_email
import RPi.GPIO as io
from p_check import p_check


class Valve:
    # class attributes

    def __init__(self, name, out, led):
        self.name = name
        self.out = out
        self.led = led
     
    def __str__(self):
        return self.name
        

class Sensor:
    # class attributes

    def __init__(self, name, IN, led):
        self.name = name
        self.IN = IN
        self.led = led


# setup pins
io.setmode(io.BCM)

# set pins for output
# Lock off
io.setup(22, io.OUT)
# V1 relay
io.setup(23, io.OUT)
# V2 relay
io.setup(24, io.OUT)
# V3 relay
io.setup(26, io.OUT)
# V4 relay
io.setup(27, io.OUT)
# Input LED
io.setup(20, io.OUT)
# Output LED
io.setup(21, io.OUT)
# V1 LED
io.setup(5, io.OUT)
# V2 LED
io.setup(6, io.OUT)
# V3 LED
io.setup(13, io.OUT)
# V4 LED
io.setup(19, io.OUT)

# set pins for inputs from micro-switches

# lock off indicator
io.setup(16, io.IN, pull_up_down=io.PUD_DOWN)
# input indicator
io.setup(17, io.IN, pull_up_down=io.PUD_DOWN)
# output indicator
io.setup(18, io.IN, pull_up_down=io.PUD_DOWN)

# set outputs pin position 0/1
# Relays
io.output(22, 1)
io.output(23, 1)
io.output(24, 1)
io.output(26, 1)
io.output(27, 1)
# LED
io.output(20, 0)
io.output(21, 0)
io.output(5, 0)
io.output(6, 0)
io.output(13, 0)
io.output(19, 0)

v0 = Valve("Lockoff", 22, 0)
v1 = Valve("v1", 23, 5)
v2 = Valve("v2", 24, 6)
v3 = Valve("v3", 26, 13)
v4 = Valve("v4", 27, 19)

S0 = Sensor("Input to box", 16, 0)
S1 = Sensor("Input to RVM", 17, 20)
S2 = Sensor("Output From RVM", 18, 21)
try:
	#LED Check
	print("LED TEST")
	print("Check all LED's are on")
	io.output(v1.led, 1)
	io.output(v2.led, 1)
	io.output(v3.led, 1)
	io.output(v4.led, 1)
	io.output(S2.led, 1)
	io.output(S1.led, 1)
	input("PRESSS ENTER TO CONTINUE")
	io.output(v1.led, 0)
	io.output(v2.led, 0)
	io.output(v3.led, 0)
	io.output(v4.led, 0)
	io.output(S2.led, 0)
	io.output(S1.led, 0)

	#valve + led test
	print("Valve Test")
	print("Check the valves are operating sequecially 1-4")
	cyclelist = [v1,v2,v3,v4]
	y=0
	for y in range(0,6):
		for x in cyclelist:
			# v# turns on
			io.output(x.out, 0)
			io.output(x.led, 1)
			time.sleep(.5)
			# v# turns off
			io.output(x.out, 1)
			io.output(x.led, 0)
			y+=1

	#holdvalve test
	print( "Put your ear to the top of the test box, lisen for the internal hold test valve to pull in")
	input("press ENTER to start")
	y=0	
	for y in range(0,5):
		io.output(v0.out, 0)
		time.sleep(0.5)
		io.output(v0.out, 1)
		time.sleep(0.5)
		y+=1
	
	

finally:
	#cleanup

	io.output(v0.out, 1)
	# De-energise all 4 coils+leds
	io.output(v1.out, 1)
	io.output(v1.led, 0)
	io.output(v2.out, 1)
	io.output(v2.led, 0)
	io.output(v3.out, 1)
	io.output(v3.led, 0)
	io.output(v4.out, 1)
	io.output(v4.led, 0)
	# input and output leds off
	io.output(S2.led, 0)
	io.output(S1.led, 0)
	io.cleanup()


