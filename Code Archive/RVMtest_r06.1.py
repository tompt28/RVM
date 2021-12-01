#!/usr/bin/env python
# coding: utf-8
#r04 fully working test script, messy sql database 
#r05 addition of output microswitch to catch unseen errors that would cause a failure of safety function. if input indicator ==1 then output indicator during PHT & CT  should == 1     
#r06 tidy up of SQL database format - seperate tables for overview and test data. frequency of writing to each.

import sqlite3
from sqlite3 import Error
import RPi.GPIO as io 
import os
import time, datetime

#setup pins 
io.setmode(io.BCM) 

#set pins for output
io.setup(23,io.OUT)
io.setup(24,io.OUT)
io.setup(26,io.OUT)
io.setup(27,io.OUT)

#set pins for input
io.setup(17, io.IN, pull_up_down=io.PUD_DOWN)
io.setup(18, io.IN, pull_up_down=io.PUD_DOWN)

#set outputs pin position 0/1
io.output(23,1)
io.output(24,1)
io.output(26,1)
io.output(27,1)

#set global variables
testGo = False
testIn = {}
i = 0
switchTime = 0.5
errorLog = []
errorCount = 0

def holdTest(hold_duration):
    """
    check for a pressure input signal using microswitches 
    """

    global errorCount
    if io.input(17) == 1:
        #energise all 4 coils
        io.output(23,0)
        io.output(24,0)
        io.output(26,0)
        io.output(27,0)
        #time deley for mechanical responce
        time.sleep(1.0)
        # check to see an output signal as expected. if none fail test and interupt, write to sql.
        if io.input(18) == 0:

            errorCount +=1
            c.execute("SELECT datetime('now','localtime')")
            timeStamp = c.fetchone()[0]

            print("test failed no output found")
            errorLog.append(datetime.datetime.now())
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_Count=?,end_date=?",("Fail","Fail","no pressure registered at output test failed",errorCount,timeStamp))

            conn.commit()

            #De-energise all 4 coils
            io.output(23,1)
            io.output(24,1)
            io.output(26,1)
            io.output(27,1) 

            raise KeyboardInterrupt
    
        # if signal on output wait for the hold duration
        time.sleep(hold_duration)

        # make sure the input and output ports still have pressure after hold
        if io.input(17) == 1 and io.input(18) == 1:
                        
            c.execute("UPDATE overview SET hold_test_Pass=?",("Pass",))
            conn.commit()

            return True

        elif io.input(17) == 1 and io.input(18) == 0:

            errorCount +=1
            print("Pressure lost over the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            timeStamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error=?,end_date",("Fail","Fail","Pressure lost over the hold duration check for leaks",errorCount,timeStamp))
        
            conn.commit()

            #De-energise all 4 coils
            io.output(23,1)
            io.output(24,1)
            io.output(26,1)
            io.output(27,1) 

            raise KeyboardInterrupt
        else:
            errorCount +=1
            print("Pressure lost over the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            timeStamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,errorCount=?,end_date",("Fail","Fail","Pressure lost over the hold duration check for leaks",errorCount,timeStamp))
        
            conn.commit()

            #De-energise all 4 coils
            io.output(23,1)
            io.output(24,1)
            io.output(26,1)
            io.output(27,1)             
                    
            return False
    else:   
        errorCount +=1
        print("No pressure found at input, Please start again.")
        errorLog.append(datetime.datetime.now())

        c.execute("SELECT datetime('now','localtime')")
        timeStamp= c.fetchone()[0]
        c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,errorCount=?,end_date",("Fail","Fail","Pressure lost over the hold duration check for leaks",errorCount,timeStamp))
       
        conn.commit()

        #De-energise all 4 coils
        io.output(23,1)
        io.output(24,1)
        io.output(26,1)
        io.output(27,1) 
       
        
        raise KeyboardInterrupt

        return False


#main program

try:
    tester = input("please enter your name or ID:") 

    hold_days =-1
    while not hold_days in range(0,365,1):
        try:
            hold_days = int(input("please enter how many days to hold test for (0-365):"))
        except ValueError:
            print("Enter a number between 0 and 365 days")

    
    hold_hrs =-1
    while not hold_hrs in range(0,24,1):
        try:
            hold_hrs = int(input("Please enter how many hours to hold test for (0-23):"))
        except ValueError:
            print("Enter a number between 0 and 23 hours")
    
    hold_min=-1
    while not hold_min in range(0,60,1):
        try:
            hold_min = int(input("Please enter how many minutes to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 minutes")
    
    hold_sec =-1
    while not hold_sec in range(0,60,1):
        try:
            hold_sec = int(input("Please enter how many seconds to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 seconds")
    
    i_max =-1
    while not i_max in range(1,10000000,1):
        try:
            i_max = int(input("Please enter how many cycles to run (1-10,000,000):"))
        except ValueError:
            print("Enter a number between 1 and 10,000,000")
    

    hold_duration = (hold_sec)+(hold_min*60)+(hold_hrs*3600)+(hold_days*24*3600)
    
    testIn = {"hold_days":hold_days,"hold_hrs":hold_hrs,"hold_min":hold_min,"hold_sec":hold_sec,"i_max":i_max}
    
    print(tester)
    
    print(testIn)
    
    input("Press Enter to start the test")

    start = datetime.datetime.now()

    fileName = "/home/pi/RVM/Database_files/%s.sqlite" %start
    print(fileName)

    #initialise cycle counter
    i=1
    
    conn=sqlite3.connect(fileName)
    c=conn.cursor()

    #sqlite timeStamp
    c.execute("SELECT datetime('now','localtime')")
    timeStamp=c.fetchone()[0]

    if __name__ == '__main__':
        
        database = "/home/pi/RVM/Database_files/%s.db" %start

        table_create_overview = '''CREATE TABLE IF NOT EXISTS overview (
                        id integer PRIMARY KEY,
                        name text ,
                        begin_date text ,
                        end_date text ,
                        hold_duration integer ,
                        hold_test_Pass text ,
                        cycles_target integer ,
                        cycles_complete integer ,
                        error_count integer,
                        cycle_test_Pass text ,
                        notes text
                        )'''
        
        table_create_testData = '''CREATE TABLE IF NOT EXISTS testData (
                        cycle_number integer PRIMARY KEY,
                        cycle_start integer,
                        cycle_end integer,
                        error integer,
                        notes text
                        )''' 

        if conn is not None:

            # create testData & overview table
            """ create a table from the create_table_sql statement
            :param conn: Connection object
            :param create_table_sql: a CREATE TABLE statement
            :return:
            """
            c.execute(table_create_overview)

            c.execute(table_create_testData)

        else:
            print("Error! cannot create the database connection.")
                
        c.execute("INSERT INTO overview (name,begin_date,hold_duration,cycles_target,error_count) VALUES(?,?,?,?,?)",(tester,start,hold_duration,i_max,errorCount))
        
        conn.commit()

        testGo = holdTest(hold_duration)
        outputOn = io.input(18)

        while i <= i_max:
           
            if testGo == False:

                errorCount+=1
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                timeStamp = c.fetchone()[0]
               
                c.execute("UPDATE testData SET error=?,notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",(errorCount,"input pressure lost- Test Paused"))
                c.execute("UPDATE overview SET error_count=?,notes=?",(errorCount,"input pressure lost- Test Paused"))
                conn.commit()
                
                while io.input(17) == 0:      
              
                    time.sleep(0.5)
                    testGo = io.input(17)
              
            elif outputOn == False:
                errorCount+=1
                print("Test failed Output has been lost ")
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                timeStamp= c.fetchone()[0]
                c.execute("UPDATE testData SET error=?,notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",(errorCount,"no pressure registered at output- Test failed",))
                c.execute("UPDATE overview SET cycle_test_Pass=?,notes=?,end_date=?",("Fail","no pressure registered at output- Test failed",timeStamp))
                               
                conn.commit()

                #De-energise all 4 coils
                io.output(23,1)
                io.output(24,1)
                io.output(26,1)
                io.output(27,1) 
                
                break

            else:
                c.execute("SELECT datetime('now','localtime')")
                timeStamp = c.fetchone()[0]

                c.execute("INSERT INTO testData (cycle_start) VALUES(?)",(timeStamp,))
                #v1 turns off
                io.output(23,1) 
                time.sleep(switchTime)
                #v1 turns on
                io.output(23,0)
                time.sleep(switchTime)

                #v2 turns off
                io.output(24,1)
                time.sleep(switchTime)
                #V2 turns on
                io.output(24,0)
                time.sleep(switchTime)

                #V3 turns off
                io.output(26,1)
                time.sleep(switchTime)
                #V3 turns on
                io.output(26,0)
                time.sleep(switchTime)

                #V4 turns off
                io.output(27,1)
                time.sleep(switchTime)
                #V4 turns on 
                io.output(27,0)
                time.sleep(switchTime)

                # check for input
                # check for output
                testGo = io.input(17)
                # check for output ==1 if input ==1  but output == 0 there is an instant fail
                outputOn = io.input(18)
        
                #sqlite timeStamp
                c.execute("SELECT datetime('now','localtime')")
                timeStamp = c.fetchone()[0]

                c.execute("UPDATE testData SET cycle_end=? WHERE cycle_number=(SELECT MAX(cycle_number) FROM testData)",(timeStamp,))
                c.execute("UPDATE overview SET cycle_test_Pass=?,cycles_complete=?,error_count=?",("Pass",i,errorCount))
                conn.commit()

                # add one to the counter
                i+=1

        end = datetime.datetime.now()
        c.execute("SELECT datetime('now','localtime')")
        timeStamp = c.fetchone()[0]
        c.execute("UPDATE overview SET end_date=?",(timeStamp,))
        conn.commit()
        print(end - start)
       
        if errorLog == []:
            print("No Errors Occured")
        else:
            print(errorLog)
        conn.close()


#what happens when you hit ctl-c
except KeyboardInterrupt:
    print('\n', i)
    print("test ended using keyboard interupt")
    
#cleanup
finally:
    io.cleanup()
    
