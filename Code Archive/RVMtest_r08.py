#!/usr/bin/env python# coding: utf-8
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
switchTime = 0.5
errorLog = []
errorCount = 0
majorError = 0

def hold_test(hold_duration):
    """
    check for a pressure input signal using microswitches
    """
    global errorCount

    if io.input(16) == 1:
        #print("got past the first check")
        io.output(22, 0)
        time.sleep(0.5)
    else:
        errorCount += 1
        print("No mains air available - try again")
        raise KeyboardInterrupt

    if io.input(17) == 1:
        #energise all 4 coils
        io.output(23, 0)
        io.output(24, 0)
        io.output(26, 0)
        io.output(27, 0)
        #time delay for mechanical responce
        time.sleep(1)

        # check to see an output signal as expected. if none fail test and interupt, write to sql


        #############################################SESNSOR


        if io.input(18) == 0:

            errorCount += 1
            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            print("test failed no output found")
            errorLog.append(datetime.datetime.now())
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_Count=?,end_date=?",
                      ("Fail", "Fail", "no pressure registered at output test failed", errorCount, time_stamp))

            conn.commit()

            #De-energise all 4 coils
            io.output(23, 1)
            io.output(24, 1)
            io.output(26, 1)
            io.output(27, 1)

            raise KeyboardInterrupt
        # close the pressure lock off valve 
        io.output(22, 1)
        # if signal on output wait for the hold duration
        time.sleep(hold_duration)

        # make sure the input and output ports still have pressure after hold no leaks 
        if io.input(17) == 1 and io.input(18) == 1:

            c.execute("UPDATE overview SET hold_test_Pass=?", ("Pass", ))
            conn.commit()

            #open the lock off vavle ready for the cycle test
            io.output(22, 0)
            return True

        elif io.input(17) == 1 and io.input(18) == 0:

            errorCount += 1
            print("Pressure lost over the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_Count=?,end_date=?",
                      ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", errorCount, time_stamp))

            conn.commit()

            #De-energise all 4 coils
            io.output(23, 1)
            io.output(24, 1)
            io.output(26, 1)
            io.output(27, 1)

            raise KeyboardInterrupt
        else:
            errorCount += 1
            print("Pressure lost over the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_count=?,end_date=?",
                      ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", errorCount, time_stamp))

            conn.commit()

            #De-energise all 4 coils
            io.output(23, 1)
            io.output(24, 1)
            io.output(26, 1)
            io.output(27, 1)

            return False
    else:
        errorCount += 1
        print("No pressure found at input, Please start again.")
        errorLog.append(datetime.datetime.now())

        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]
        c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_count=?,end_date=?",
                  ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", errorCount, time_stamp))

        conn.commit()

        #De-energise all 4 coils
        io.output(23, 1)
        io.output(24, 1)
        io.output(26, 1)
        io.output(27, 1)

        raise KeyboardInterrupt

#main program

try:
    tester = input("please enter your name or ID:")

    hold_days = - 1
    while not hold_days in range(0, 365, 1):
        try:
            hold_days = int(input("please enter how many days to hold test for (0-365):"))
        except ValueError:
            print("Enter a number between 0 and 365 days")

    hold_hrs = - 1
    while not hold_hrs in range(0, 24, 1):
        try:
            hold_hrs = int(input("Please enter how many hours to hold test for (0-23):"))
        except ValueError:
            print("Enter a number between 0 and 23 hours")

    hold_min = - 1
    while not hold_min in range(0, 60, 1):
        try:
            hold_min = int(input("Please enter how many minutes to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 minutes")

    hold_sec = - 1
    while not hold_sec in range(0, 60, 1):
        try:
            hold_sec = int(input("Please enter how many seconds to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 seconds")

    i_max = - 1
    while not i_max in range(1, 10000001, 1):
        try:
            i_max = int(input("Please enter how many cycles to run (1-10,000,000):"))
        except ValueError:
            print("Enter a number between 1 and 10,000,000")

    hold_duration = (hold_sec) + (hold_min * 60) + (hold_hrs * 3600) + (hold_days * 24 * 3600)

    testIn = {"hold_days":hold_days, "hold_hrs":hold_hrs, "hold_min":hold_min,
              "hold_sec":hold_sec, "i_max":i_max}

    print(tester)

    print(testIn)

    input("Press Enter to start the test")

    start = datetime.datetime.now()

    fileName = "/home/pi/RVM/Database_files/%s.sqlite" %start
    print(fileName)

    #initialise cycle counter
    i = 1

    conn = sqlite3.connect(fileName)
    c = conn.cursor()

    #sqlite time_stamp
    c.execute("SELECT datetime('now','localtime')")
    time_stamp = c.fetchone()[0]

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
                        major_error integer,
                        cycle_test_Pass text ,
                        notes text
                        )'''

        table_create_testData = '''CREATE TABLE IF NOT EXISTS testData (
                        cycle_number integer PRIMARY KEY,
                        cycle_start integer,
                        v1 text,
                        v2 text,
                        v3 text,
                        v4 text,
                        cycle_end integer,
                        error integer,
                        major_error integer,
                        notes text
                        )'''

        if conn is not None:

            """ create a table from the create_table_sql statement
            :param conn: Connection object
            :param create_table_sql: a CREATE TABLE statement
            :return:
            """
            c.execute(table_create_overview)

            c.execute(table_create_testData)

        else:
            print("Error! cannot create the database connection.")

        c.execute("INSERT INTO overview (name,begin_date,hold_duration,cycles_target,error_count) VALUES(?,?,?,?,?)",
                  (tester, start, hold_duration, i_max, errorCount))

        conn.commit()

        testGo = hold_test(hold_duration)
        outputOn = io.input(18)

        while i <= i_max:

            if testGo == False:

                errorCount += 1
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute("UPDATE testData SET error=?,notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                          (errorCount, "input pressure lost- Test Paused"))
                c.execute("UPDATE overview SET error_count=?,notes=?",
                          (errorCount, "input pressure lost- Test Paused"))
                conn.commit()

                while io.input(17) == 0:

                    time.sleep(0.5)
                    testGo = io.input(17)

            elif outputOn == False:

                majorError += 1
                print("Test failed Output has been lost ")
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]
                c.execute("UPDATE testData SET major_error=?,notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                          (errorCount, "no pressure registered at output- Test failed",))
                c.execute("UPDATE overview SET cycle_test_Pass=? major_error=?,notes=?,end_date=?",
                          ("Fail", majorError, "no pressure registered at output- Test failed", time_stamp))

                conn.commit()

            else:
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute("INSERT INTO testData (cycle_start) VALUES(?)", (time_stamp, ))

                #v1 turns off
                io.output(23, 1)
                time.sleep(switchTime)
                #v1 turns on
                io.output(23, 0)
                time.sleep(switchTime)
                # check for input
                testGo = io.input(17)
                # check for output ==1 if input ==1  but output == 0 there is an instant fail
                outputOn = io.input(18)
                c.execute("UPDATE testData SET v1=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                          ("Pass",))

                #v2 turns off
                io.output(24, 1)
                time.sleep(switchTime)
                #V2 turns on
                io.output(24, 0)
                time.sleep(switchTime)
                # check for input
                testGo = io.input(17)
                # check for output ==1 if input ==1  but output == 0 there is an instant fail
                outputOn = io.input(18)
                c.execute("UPDATE testData SET v2=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                          ("Pass",))

                #V3 turns off
                io.output(26, 1)
                time.sleep(switchTime)
                #V3 turns on
                io.output(26, 0)
                time.sleep(switchTime)
                # check for input
                testGo = io.input(17)
                # check for output ==1 if input ==1  but output == 0 there is an instant fail
                outputOn = io.input(18)
                c.execute("UPDATE testData SET v3=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                          ("Pass",))
                #V4 turns off
                io.output(27, 1)
                time.sleep(switchTime)
                #V4 turns on
                io.output(27, 0)
                time.sleep(switchTime)
                # check for input
                testGo = io.input(17)
                # check for output ==1 if input ==1  but output == 0 there is an instant fail
                outputOn = io.input(18)
                c.execute("UPDATE testData SET v4=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                          ("Pass",))

                #sqlite time_stamp
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute("UPDATE testData SET cycle_end=? WHERE cycle_number=(SELECT MAX(cycle_number) FROM testData)", (time_stamp, ))
                c.execute("UPDATE overview SET cycle_test_Pass=?,cycles_complete=?,error_count=?",
                          ("Pass", i, errorCount))
                conn.commit()

                # add one to the counter
                i += 1

        io.output(22, 1)
        end = datetime.datetime.now()
        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]
        c.execute("UPDATE overview SET end_date=?", (time_stamp,))
        conn.commit()
        print(end - start)

        if errorLog == []:
            print("No Errors Occured")
        else:
            print(errorLog)
        conn.close()


#what happens when you hit ctl-c
except KeyboardInterrupt:
    io.output(22, 1)
    print('\n', i)
    print("test ended using keyboard interupt")

#cleanup
finally:
    io.cleanup()
