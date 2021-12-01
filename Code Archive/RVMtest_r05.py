#!/usr/bin/env python
# coding: utf-8
#r_04 fully working test script, messy sql database 
#r_05 addition of output microswitch to catch unseen errors that would cause a failure of safety function. if input indicator ==1 then output indicator during PHT & CT  should == 1     

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
switchTime = 0.25
errorLog = []

def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:  
        print(e)

def holdTest(hold_duration):
    """
    check for a pressure input signal using microswitches 
    """

    if io.input(17) == 1:
        #energise all 4 coils
        io.output(23,0)
        io.output(24,0)
        io.output(26,0)
        io.output(27,0)
        #time deley for mechanical responce
        time.sleep(.5)
        # check to see an output signal as expected. if none fail test and interupt write to sql.
        if io.input(18)==0:
            print("test failed no output found")
            errorLog.append(datetime.datetime.now())
            c.execute("UPDATE testData SET hold_test_results=?,notes=?",("Failed","no pressure registered at output test failed"))
            
            c.execute("SELECT datetime('now','localtime')")
            timeStamp= c.fetchone()[0]
            c.execute("INSERT INTO testData (notes,cycle_test_results,cycle_no,end_date) VALUES(?,?,?,?)",("All solenoids energised and no output from specimen","Failed",i,timeStamp))
            conn.commit()
            #De-energise all 4 coils
            io.output(23,1)
            io.output(24,1)
            io.output(26,1)
            io.output(27,1) 
            raise KeyboardInterrupt
        else:
            pass

        # if signal on output wait for the hold duration
        time.sleep(hold_duration)
        if io.input(17) == 1:
                        
            c.execute("UPDATE testData SET hold_test_results=?",("Passsed",))
            conn.commit()

            return True

        else: 
            print("Pressure at Input lost over the hold duration- Pressure hold test failed")
            errorLog.append(datetime.datetime.now())
            c.execute("UPDATE testData SET hold_test_results=?,notes=?",("Failed","Pressure at Input lost over the hold duration- Pressure hold test failed"))
            
            c.execute("SELECT datetime('now','localtime')")
            timeStamp= c.fetchone()[0]
            c.execute("INSERT INTO testData (notes,cycle_test_results,cycle_no,end_date) VALUES(?,?,?,?)",("Test ended before before completion","Failed",i,timeStamp))
            conn.commit()
            #De-energise all 4 coils
            io.output(23,1)
            io.output(24,1)
            io.output(26,1)
            io.output(27,1) 
            raise KeyboardInterrupt
                    
            return False
    else:   

        print("No pressure found at input, Please start again.")
        c.execute("UPDATE testData SET hold_test_results=?,notes=?",("Failed","No pressure found at input, Please start again."))
        c.execute("SELECT datetime('now','localtime')")     
        timeStamp=c.fetchone()[0]
        c.execute("INSERT INTO testData (notes,cycle_test_results,cycle_no,end_date) VALUES(?,?,?,?)",("Test ended before before completion","Failed",i,timeStamp))
        conn.commit()
        conn.commit()
        #De-energise all 4 coils
        io.output(23,1)
        io.output(24,1)
        io.output(26,1)
        io.output(27,1) 
        c.execute("SELECT datetime('now','localtime')")
        
        raise KeyboardInterrupt
    

#main program

try:
    tester = input("please enter your name or ID:") 

    hold_days=-1
    while not hold_days in range(0,365,1):
        try:
            hold_days = int(input("please enter how many days to hold test for (0-365):"))
        except ValueError:
            print("Enter a number between 0 and 365 days")

    
    hold_hrs=-1
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
    
    hold_sec=-1
    while not hold_sec in range(0,60,1):
        try:
            hold_sec = int(input("Please enter how many seconds to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 seconds")
    
    i_max=-1
    while not i_max in range(1,10000000,1):
        try:
            i_max = int(input("Please enter how many cycles to run (1-10,000,000):"))
        except ValueError:
            print("Enter a number between 1 and 10,000,000")
    

    hold_duration = (hold_sec)+(hold_min*60)+(hold_hrs*3600)+(hold_days*24*3600)
    
    testIn={"hold_days":hold_days,"hold_hrs":hold_hrs,"hold_min":hold_min,"hold_sec":hold_sec,"i_max":i_max}
    
    print(tester)
    
    print(testIn)
    
    input("Press Enter to start the test")

    start = datetime.datetime.now()

    fileName="/home/pi/RVM/Database_files/%s.sqlite" %start
    print(fileName)

    #initialise cycle counter
    i=0
    
    conn=sqlite3.connect(fileName)
    c=conn.cursor()

    #sqlite timestamp
    c.execute("SELECT datetime('now','localtime')")
    timeStamp=c.fetchone()[0]

    if __name__ == '__main__':
        
        database = "/home/pi/RVM/Database_files/%s.db" %start

        table_create = '''CREATE TABLE IF NOT EXISTS testData (
                        id integer PRIMARY KEY,
                        name text ,
                        test_setup_sec integer ,
                        test_setup_min integer ,
                        test_setup_hrs integer ,
                        test_setup_days integer ,
                        test_setup_imax integer ,
                        cycle_no integer,
                        error_time integer,
                        hold_test_results text,
                        cycle_test_results text,
                        begin_date text,
                        end_date text,
                        notes text
                        )'''
                
        if conn is not None:
            # create testData table
            """ create a table from the create_table_sql statement
            :param conn: Connection object
            :param create_table_sql: a CREATE TABLE statement
            :return:
            """
            c.execute(table_create)
        else:
            print("Error! cannot create the database connection.")
                
        c.execute("INSERT INTO testData (name,test_setup_sec,test_setup_min,test_setup_hrs,test_setup_days,test_setup_imax,begin_date) VALUES(?,?,?,?,?,?,?)",(tester,hold_sec,hold_min,hold_hrs,hold_days,i_max,start))
        
        conn.commit()

        testGo=holdTest(hold_duration)

         
        while i < i_max and io.input(18)==1 :
            if testGo==False:
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                timeStamp=c.fetchone()[0]
                c.execute("INSERT INTO testData (error_time,cycle_no) VALUES(?,?)",(timeStamp,i))
                conn.commit()
                while io.input(17)==0:      
                    time.sleep(0.5)
                    testGo=io.input(17)
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                timeStamp=c.fetchone()[0]
                c.execute("INSERT INTO testData (error_time) VALUES(?)",(timeStamp,))
                conn.commit()
            else:
                #v1 turns off
                io.output(23,1) 
                time.sleep(switchTime)
                #v1 turns on
                io.output(23,0)

                #v2 turns off
                io.output(24,1)
                time.sleep(switchTime)
                #V2 turns on
                io.output(24,0)

                #V3 turns off
                io.output(26,1)
                time.sleep(switchTime)
                #V3 turns on
                io.output(26,0)

                #V4 turns off
                io.output(27,1)
                time.sleep(switchTime)
                #V4 turns on 
                io.output(27,0)

                # check for an input
                testGo=io.input(17)
                # add one to the counter
                i+=1
                #sqlite timestamp
                c.execute("SELECT datetime('now','localtime')")
                timeStamp=c.fetchone()[0]
                c.execute("INSERT INTO testData (cycle_test_results,end_date,cycle_no) VALUES(?,?,?)",("Pass",timeStamp,i))
                conn.commit()
        else:
            print("Test failed Output has been lost found")
            errorLog.append(datetime.datetime.now())
            c.execute("UPDATE testData SET hold_test_results=?,notes=?",("Failed","no pressure registered at output test failed"))
            
            c.execute("SELECT datetime('now','localtime')")
            timeStamp= c.fetchone()[0]
            c.execute("INSERT INTO testData (notes,cycle_test_results,cycle_no,end_date) VALUES(?,?,?,?)",("An instance occured where there was no output from specimen","Failed",i,timeStamp))
            conn.commit()
            #De-energise all 4 coils
            io.output(23,1)
            io.output(24,1)
            io.output(26,1)
            io.output(27,1) 
            raise KeyboardInterrupt


        c.execute("SELECT datetime('now','localtime')")
        timeStamp=c.fetchone()[0]
        c.execute("INSERT INTO testData (name,test_setup_sec,test_setup_min,test_setup_hrs,test_setup_days,test_setup_imax,cycle_no,begin_date,end_date) VALUES(?,?,?,?,?,?,?,?,?)",(tester,hold_sec,hold_min,hold_hrs,hold_days,i_max,i,start,timeStamp))
        conn.commit()
        end = datetime.datetime.now()
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
    
