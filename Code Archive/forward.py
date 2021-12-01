#!/usr/bin/env python
# coding: utf-8
#r04 - fully working test script, messy sql database
#r05 - addition of output microswitch to catch unseen errors that would cause a failure of
        #safety function. If input indicator ==1 then output indicator during Hold & Cycle should == 1
#r06 - tidy up of SQL database format - seperate tables for overview and test data.
        #frequency of writing to each table
#r07 - addition of lock off vavle. any failures or ending the test closes lock off and terminates.
#r08 - test no longer terminates on loss of output notification and hold for enter. logs a major error but continues.

import sqlite3
import time, datetime
import os
import RPi.GPIO as io

#setup pins
io.setmode(io.BCM)

#set pins for output

#Lockoff
io.setup(22, io.OUT)
#V1 relay
io.setup(23, io.OUT)
#V2 relay
io.setup(24, io.OUT)
#V3 relay
io.setup(26, io.OUT)
#V4 relay
io.setup(27, io.OUT)

#set pins for inputs from microswitches

#lockoff indicator
io.setup(16, io.IN, pull_up_down=io.PUD_DOWN)
#input indicator
io.setup(17, io.IN, pull_up_down=io.PUD_DOWN)
#output indicator
io.setup(18, io.IN, pull_up_down=io.PUD_DOWN)

#set outputs pin position 0/1
io.output(22, 1)
io.output(23, 1)
io.output(24, 1)
io.output(26, 1)
io.output(27, 1)

#set global variables
testGo = False
testIn = {}
i = 0
switchTime = 0.25
errorLog = []
errorCount = 0
major_error = 0

try:
    if io.input(16) == 1:
        #print("got past the first check")
        io.output(22, 0)
        time.sleep(0.5)
        io.output(23, 0)
        io.output(24, 0)
        io.output(26, 0)
        io.output(27, 0)
        io.output(22,1) 

#what happens when you hit ctl-c
except KeyboardInterrupt:
    io.output(22, 1)
    print('\n', i)
    print("test ended using keyboard interupt")

#cleanup
finally:
    io.cleanup()

