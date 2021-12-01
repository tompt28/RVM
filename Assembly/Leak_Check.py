#!/usr/bin/env python
# coding: utf-8

import datetime
import time
import RPi.GPIO as io



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

# set variables
testGo = False
i = 0
i_max = 5
switchTime = 1
bar = []
errorLog = []
errorCount = 0
major_error = 0
cyclelist = [v1, v2, v3, v4]
Scenario_cycle = 0
Scenario_cycle_max=5
Scenario_dict = {"1": [v1, v2], "2": [v1, v3], "3": [v1, v4], "4": [v2, v3], "5": [v2, v4],
                 "6": [v3, v4]}


# main program
try:
    # initialise cycle counter
    i = 1
    # make sure all on!
    
    io.output(v0.out, 0)
    # energise all 4 coils+leds
    io.output(v1.out, 0)
    io.output(v1.led, 1)
    io.output(v2.out, 0) 
    io.output(v2.led, 1)
    io.output(v3.out, 0)
    io.output(v3.led, 1)
    io.output(v4.out, 0)
    io.output(v4.led, 1)
    # input and output leds on
    io.output(S2.led, 1)
    io.output(S1.led, 1)
    
    input("press enter to cycle on and off" )
    
    for x in range(0,10,1):
        # de energise all 4 coils+leds
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
        
        time.sleep(1)
        
        io.output(v1.out, 0)
        io.output(v1.led, 1)

        io.output(v2.out, 0)
        io.output(v2.led, 1)
        io.output(v3.out, 0)
        io.output(v3.led, 1)
        io.output(v4.out, 0)
        io.output(v4.led, 1)
        # input and output leds on
        io.output(S2.led, 1)
        io.output(S1.led, 1)
        
        time.sleep(1)
        
        x+=1
        
    input("press enter to cycle valves" )
    
    while i <= i_max:
    
        for x in cyclelist:
            # v# turns off
            io.output(x.out, 1)
            io.output(x.led, 0)
            time.sleep(switchTime)

                
            # v# turns on
            io.output(x.out, 0)
            io.output(x.led, 1)
            time.sleep(switchTime)
       
                    

        print("Cycle:",i, ": pass")

        # add one to the cycle counter
        i += 1

    io.output(v0.out, 1)

    # make sure all off!
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

    #############################################################################################
    #Scenario testing
    
    #all on
    io.output(v0.out, 0)
    # energise all 4 coils+leds
    io.output(v1.out, 0)
    io.output(v1.led, 1)
    io.output(v2.out, 0)
    io.output(v2.led, 1)
    io.output(v3.out, 0)
    io.output(v3.led, 1)
    io.output(v4.out, 0)
    io.output(v4.led, 1)
    # input and output leds on
    io.output(S2.led, 1)
    io.output(S1.led, 1)
    testGo =  True
    
    while Scenario_cycle < Scenario_cycle_max:
        #Double drop out
        for k, x in Scenario_dict.items():
           
            for z in range (0,2):
                print("-")
                if x[z] == v1:
                    print("V1 OFF:")
                elif x[z] == v2:
                    print("V2 OFF:")
                elif x[z] == v3:
                    print("V3 OFF:")
                elif x[z] == v4:
                    print("V4 OFF:")
            
            # v# and LED# turns off
            io.output(x[0].out, 1)
            io.output(x[1].out, 1)
            io.output(x[0].led, 0)
            io.output(x[1].led, 0)
            time.sleep(switchTime)

            
            
            # turn tested SOV back on
            io.output(x[0].out, 0)
            io.output(x[1].out, 0)
            io.output(x[0].led, 1)
            io.output(x[1].led, 1)
            time.sleep(switchTime)
   

        Scenario_cycle+=1

    print("all Scenarios Passed")

####################################################################################
#end of testing

    print("Testing Completed")

# what happens when you hit ctl-c
except KeyboardInterrupt:
    print("test ended")
    print("\n", "Major errors count: ", major_error)
    print("\n", "minor errors count: ", errorCount)
    print("\n", "cycles completed = ", i)

# cleanup
finally:
    # make sure all off!
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
