import datetime
import time
import csv
#import pandas
import RPi.GPIO as io

class Valve:
    # class attributes

    def __init__(self, name, out, led):
        self.name = name
        self.out = out
        self.led = led


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

#instaciate the valves and sensors
v0 = Valve("Lockoff", 22, 0)
v1 = Valve("valve #1", 23, 5)
v2 = Valve("valve #2", 24, 6)
v3 = Valve("valve #3", 26, 13)
v4 = Valve("valve #4", 27, 19)

S0 = Sensor("Input to box", 16, 0)
S1 = Sensor("Input to RVM", 17, 20)
S2 = Sensor("Output From RVM", 18, 21)

# main program
try:      
        
    start_time = 0
    end_time = 0
    results=[]
    output = False  
    io.output(v0.out, 0)


    for x in range(0,10):
        
        start_time = datetime.datetime.now()
        #print("start:",start_time)
        io.output(v1.out, 0)
        io.output(v2.out, 0)
        io.output(v3.out, 0)
        io.output(v4.out, 0)
        
        while not output:
        
            if io.input(S2.IN):                     
               output = True 
               
        end_time = datetime.datetime.now() 

        #print("end",end_time)
       
        time.sleep(2)
        io.output(v1.out, 1)          
        io.output(v2.out, 1)
        io.output(v3.out, 1)
        io.output(v4.out, 1)

        t = str(end_time - start_time)     
        results.append(t)
               
        output = False
        time.sleep(2)
        x+=1
     
    print(results)
    with open("result.csv","w")as f:
        wr = csv.writer(f, delimiter=",",quotechar='"')
        wr.writerows(results)
    

    #f_read = pandas.read_csv("results.csv")
    #print(f_read)


# what happens when you hit ctl-c
except KeyboardInterrupt:
    print("test ended using keyboard interrupt")
    print('\n', "cycles completed = ", i)

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
