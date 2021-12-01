#!/usr/bin/env python
# coding: utf-8
# r04 - fully working test script, messy sql database
# r05 - addition of output micro-switch to catch unseen errors that would cause a failure of
# safety function. If input indicator ==1 then output indicator during Hold & Cycle should == 1
# r06 - tidy up of SQL database format - separate tables for overview and test data.
# frequency of writing to each table
# r07 - addition of lock off valve. any failures or ending the test closes lock off and terminates.
# r08 - test no longer terminates on loss of output notification and hold for enter. logs a major error but continues.
# r09 - LED integration
# r10 - Email reporting included
# r11 - Email tidy up
# r12 - tidy up
# r12.1 - functions implemented for holdtest hold duration and cycle max making it more accessible in the future

import datetime
import smtplib
import sqlite3
import ssl
import time
import RPi.GPIO as io

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

# Email reporting
port = '465'  # for secure messages
smtp_server = 'smtp.gmail.com'
sender_email = "testpi.pneumtrol@gmail.com"
receiver_email = ""
password = "Pneumatroltest1!!"

# set global variables
testGo = False
testIn = {}
i_max = -1
hold_duration = -1
switchTime = 0.25
errorLog = []
errorCount = 0
major_error = 0


def erroremail(smtp_server, port, sender_email, password, receiver_email):
    try:
        message = """
                    RVM Testing Error

                    There has been a major fault on the RVM test and output has been lost, Please review the testing. 

                    This message is sent from Python."""

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
    except Exception as e:
        print(e)


def hold_time():
    """
    asks the tester for a hold duration.
    output = hold duration
    """
    hold_days = - 1
    while hold_days not in range(0, 365, 1):
        try:
            hold_days = int(input("please enter how many days to hold test for (0-365):"))
        except ValueError:
            print("Enter a number between 0 and 365 days")

    hold_hrs = - 1
    while hold_hrs not in range(0, 24, 1):
        try:
            hold_hrs = int(input("Please enter how many hours to hold test for (0-23):"))
        except ValueError:
            print("Enter a number between 0 and 23 hours")

    hold_min = - 1
    while hold_min not in range(0, 60, 1):
        try:
            hold_min = int(input("Please enter how many minutes to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 minutes")

    hold_sec = - 1
    while hold_sec not in range(0, 60, 1):
        try:
            hold_sec = int(input("Please enter how many seconds to hold test for (0-59):"))
        except ValueError:
            print("Enter a number between 0 and 59 seconds")

    t = (hold_sec + (hold_min * 60) + (hold_hrs * 3600) + (hold_days * 24 * 3600))
    return t


def cycle_max():
    """
    Asks the user for a number of cycles to test over
    output = i_max 
    """
    x = - 1
    while x not in range(1, 10000000, 1):
        try:
            x = int(input("Please enter how many cycles to run (1-10,000,000):"))
        except ValueError:
            print("Enter a number between 1 and 10,000,000")
    return x


def hold_test(t, er, s):
    """
    check for a pressure input signal using micro-switches
    hold_duration as time in seconds
    """

    if io.input(16) == 1:
        io.output(22, 0)
        time.sleep(s)
    else:
        er += 1
        print("No mains air available - try again")
        return False, er

    if io.input(17) == 1:
        io.output(20, 1)
        # energise all 4 coils+leds
        io.output(23, 0)
        io.output(5, 1)
        io.output(24, 0)
        io.output(6, 1)
        io.output(26, 0)
        io.output(13, 1)
        io.output(27, 0)
        io.output(19, 1)
        # time delay for mechanical response
        time.sleep(s)

        if io.input(18) == 0:
            er += 1
            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            print("test failed no output found")
            errorLog.append(datetime.datetime.now())
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_Count=?,end_date=?",
                      ("Fail", "Fail", "no pressure registered at output test failed", er, time_stamp))

            conn.commit()

            # De-energise all 4 coils+leds
            io.output(23, 1)
            io.output(5, 0)
            io.output(24, 1)
            io.output(6, 0)
            io.output(26, 1)
            io.output(13, 0)
            io.output(27, 1)
            io.output(19, 0)

            return False, er

        # close the pressure lock off valve
        io.output(21, 1)
        io.output(22, 1)
        # if signal on output wait for the hold duration
        time.sleep(t)

        # make sure the input and output ports still have pressure after hold / no leaks 
        if io.input(17) == 1 and io.input(18) == 1:

            c.execute("UPDATE overview SET hold_test_Pass=?", ("Pass",))
            conn.commit()

            # open the lock off valve ready for the cycle test
            io.output(22, 0)
            return True , er

        elif io.input(17) == 1 and io.input(18) == 0:
            io.output(21, 0)
            er += 1
            print("Pressure lost over the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_Count=?,end_date=?",
                      ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", er, time_stamp))

            conn.commit()

            # De-energise all 4 coils
            input("press enter to close save and close the test")

            io.output(23, 1)
            io.output(5, 0)
            io.output(24, 1)
            io.output(6, 0)
            io.output(26, 1)
            io.output(13, 0)
            io.output(27, 1)
            io.output(19, 0)

            return False, er
        else:
            er += 1
            print("Pressure or input lost over the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_count=?,end_date=?",
                      ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", er, time_stamp))

            conn.commit()
            input("press enter to close save and close the test")

            # De-energise all 4 coils
            io.output(23, 1)
            io.output(5, 0)
            io.output(24, 1)
            io.output(6, 0)
            io.output(26, 1)
            io.output(13, 0)
            io.output(27, 1)
            io.output(19, 0)

            return False, er
    else:
        io.output(20, 0)
        er += 1
        print("No pressure found at input, Please start again.")
        errorLog.append(datetime.datetime.now())

        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]
        c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_count=?,end_date=?",
                  ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", er, time_stamp))

        conn.commit()

        input("press enter to close save and close the test")
        # De-energise all 4 coils
        io.output(23, 1)
        io.output(5, 0)
        io.output(24, 1)
        io.output(6, 0)
        io.output(26, 1)
        io.output(13, 0)
        io.output(27, 1)
        io.output(19, 0)
        io.output(21, 0)

        return False, er


# main program
try:
    tester = input("please enter your name or ID: ")

    Email = ""
    while Email == "" or Email[0] != "N" or Email[0] != "y":
        Email = input("would you like email reporting Y/N:").upper()

        if Email == "Y":
            receiver_email = str(input("what is your email address?:"))
            break
        elif Email == "N":
            receiver_email = "tompneumatrol@gmail.com"
            break
        elif Email == "":
            print("Please enter Y/N:")

        else:
            print("Please enter Y/N:")

    hold_duration = hold_time()
    i_max = cycle_max()

    print("hi {},\nIf there is a error i'll try to reach you at {},\n The hold test will run over {}s and will "
          "then perform {} cycles.".format(tester,receiver_email,hold_duration,i_max))

    input("Press Enter to start the test")

    start = datetime.datetime.now()

    fileName = "/home/pi/RVM/Database_files/%s.sqlite" % start
    print(fileName)

    conn = sqlite3.connect(fileName)
    c = conn.cursor()

    # sqlite time_stamp
    c.execute("SELECT datetime('now','localtime')")
    time_stamp = c.fetchone()[0]

    if __name__ == '__main__':

        database = "/home/pi/RVM/Database_files/%s.db" % start

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

        # initialise cycle counter
        i = 1

        holdtest = hold_test(hold_duration, errorCount, switchTime)
        errorCount = holdtest[1]
        testGo = holdtest[0]

        if not testGo:
            input("hold test failed, press enter to continue ")

        outputOn = io.input(18)

        while i <= i_max:

            if not testGo:

                errorCount += 1
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute(
                    "UPDATE testData SET error=?,notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                    (errorCount, "input pressure lost- Test Paused"))
                c.execute("UPDATE overview SET error_count=?,notes=?",
                          (errorCount, "input pressure lost- Test Paused"))
                conn.commit()

                while io.input(17) == 0:
                    time.sleep(0.5)
                    testGo = io.input(17)

            elif not outputOn:

                major_error += 1
                print("Major error Output has been lost!")
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]
                c.execute(
                    "UPDATE testData SET major_error=?,notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM "
                    "testData)",

                    (errorCount, "no pressure registered at output- Test failed",))
                c.execute("UPDATE overview SET cycle_test_Pass=?,major_error=?,notes=?,end_date=?",
                          ("Fail", major_error, "no pressure registered at output- Test failed", time_stamp))

                conn.commit()

                erroremail(smtp_server, port, sender_email, password, receiver_email)
                
                input("The output has been lost, Major error logged Press Enter to continue with test...")
                
                if not outputOn:
                    outputOn = True

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            c.execute("INSERT INTO testData (cycle_start) VALUES(?)", (time_stamp,))

            # v1 turns off
            io.output(23, 1)
            io.output(5, 0)
            time.sleep(switchTime)
            # v1 turns on
            io.output(23, 0)
            io.output(5, 1)
            time.sleep(switchTime)
            # check for input
            testGo = io.input(17)
            io.output(20, testGo)
            # check for output ==1 - if input ==1  but output == 0 there is an instant fail
            outputOn = io.input(18)
            io.output(21, outputOn)
            c.execute("UPDATE testData SET v1=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                      ("Pass",))

            # v2 turns off
            io.output(24, 1)
            io.output(6, 0)
            time.sleep(switchTime)
            # V2 turns on
            io.output(24, 0)
            io.output(6, 1)
            time.sleep(switchTime)
            testGo = io.input(17)
            io.output(20, testGo)
            # check for output ==1 - if input ==1  but output == 0 there is an instant fail
            outputOn = io.input(18)
            io.output(21, outputOn)
            c.execute("UPDATE testData SET v2=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                      ("Pass",))

            # V3 turns off
            io.output(26, 1)
            io.output(13, 0)
            time.sleep(switchTime)
            # V3 turns on
            io.output(26, 0)
            io.output(13, 1)
            time.sleep(switchTime)
            testGo = io.input(17)
            io.output(20, testGo)
            # check for output ==1 - if input ==1  but output == 0 there is an instant fail
            outputOn = io.input(18)
            io.output(21, outputOn)
            c.execute("UPDATE testData SET v3=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                      ("Pass",))
            # V4 turns off
            io.output(27, 1)
            io.output(19, 0)
            time.sleep(switchTime)
            # V4 turns on
            io.output(27, 0)
            io.output(19, 1)
            time.sleep(switchTime)
            testGo = io.input(17)
            io.output(20, testGo)
            # check for output ==1 - if input ==1  but output == 0 there is an instant fail
            outputOn = io.input(18)
            io.output(21, outputOn)
            c.execute("UPDATE testData SET v4=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM testData)",
                      ("Pass",))

            # sqlite time_stamp
            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            c.execute("UPDATE testData SET cycle_end=? WHERE cycle_number=(SELECT MAX(cycle_number) FROM testData)",
                      (time_stamp,))
            c.execute("UPDATE overview SET cycle_test_Pass=?,cycles_complete=?,error_count=?",
                      ("Pass", i, errorCount))
            conn.commit()

            # add one to the cycle counter
            i += 1

        io.output(22, 1)
        end = datetime.datetime.now()
        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]
        c.execute("UPDATE overview SET end_date=?", (time_stamp,))
        conn.commit()
        print(end - start)

        if not errorLog:
            print("No Errors Occurred")
        else:
            print(errorLog)
        conn.close()


# what happens when you hit ctl-c
except KeyboardInterrupt:
    io.output(22, 1)
    print('\n', i)
    print("test ended using keyboard interrupt")

# cleanup
finally:
    io.cleanup()
