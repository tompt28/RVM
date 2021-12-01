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
# r12.1 - functions implemented for hold test hold duration and cycle max making it more accessible in the future
# r12.2 - bug fix
# r12.3 - Fully working
# r13 - classes used for Valves allowing for iterable cycle test with consistent checks
# r14 - pressure sensor used to measure output. code separated in to modules p_check and secant
# r15 - updated to use modules and print out tidy up for user
# r16 - DB file rename & add sleep to allow restart if no mains at hold test & update DB tables.

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

# Email reporting
port = '465'  # for secure messages
smtp_server = 'smtp.gmail.com'
sender_email = "testpi.pneumatrol@gmail.com"
receiver_email = ""
password = "Pneumatroltest1!"

# set variables
testGo = False
testIn = {}
i = 0
i_max = -1
hold_duration = -1
switchTime = 0.25
errorLog = []
errorCount = 0
major_error = 0
cyclelist = [v1, v2, v3, v4]
bar = []


def open_data(f):
    """
    asks if you would like to open the data base 
    """
    data = ""
    while data == "" or data[0] != "N" or data[0] != "y":
        data = input("would you like to open the test database? please enter Y/N").upper()

        if data == "Y":
            return subprocess.Popen(['xdg-open', f])
        elif data == "N":
            break
        elif data == "":
            print("Please enter Y/N:")
        else:
            print("Please enter Y/N:")


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
    y = - 1
    while y not in range(1, 10000000, 1):
        try:
            y = int(input("Please enter how many cycles to run (1-10,000,000):"))
        except ValueError:
            print("Enter a number between 1 and 10,000,000")
    return y


def hold_test(t, er, s, pr):
    """
    check for a pressure input signal using micro-switches

    t = hold_duration as time in seconds
    er = error count
    s = switch time

    """
    c.execute("SELECT datetime('now','localtime')")
    Hold_start = c.fetchone()[0]
    c.execute("UPDATE Holdtest SET Hold_start=?", (Hold_start,))
    conn.commit()

    if io.input(S0.IN) == 1:
        io.output(v0.out, 0)
        time.sleep(s)
    else:
        while io.input(S0.IN) == 0:
            er += 1
            noIn = 0
            noIn = input("No mains air available - check the supply and press enter to try again or 'N' to close the test") 
            if noIn[0].upper() == "N":
                
                c.execute("UPDATE Holdtest SET hold_test_Pass=?, Pressure_ref=?, hold_duration=?, Pressure_held=?, Pressure_dif=?", ("Fail", 0, 0, 0, 0))
                conn.commit()
               
                return False, er
            else:
                print("Please enter Y/N:")

    if io.input(S1.IN) == 1:
        io.output(S1.led, 1)

        # energise all 4 coils+leds
        io.output(v1.out, 0)
        io.output(v1.led, 1)
        io.output(v2.out, 0)
        io.output(v2.led, 1)
        io.output(v3.out, 0)
        io.output(v3.led, 1)
        io.output(v4.out, 0)
        io.output(v4.led, 1)

        # time delay for mechanical response
        time.sleep(s)

        pr.append(p_check())
        print("Initial pressure at output = ", '{:.03f}'.format(pr[0]), "bar(g)")
        c.execute("UPDATE Holdtest SET Pressure_ref=?", (pr[0],))
        conn.commit()

        if io.input(S2.IN) == 1:
            io.output(S2.led, 1)
        else:
            while io.input(S2.IN) == 0:
                er += 1
                # De-energise all 4 coils+leds
                io.output(v1.out, 1)
                io.output(v1.led, 0)
                io.output(v2.out, 1)
                io.output(v2.led, 0)
                io.output(v3.out, 1)
                io.output(v3.led, 0)
                io.output(v4.out, 1)
                io.output(v4.led, 0)

                errorLog.append(datetime.datetime.now())
                input("No output found, Check valves are operational and there are no leaks. Press enter "
                      "to try the hold test again")

                # energise all 4 coils+leds
                io.output(v1.out, 0)
                io.output(v1.led, 1)
                io.output(v2.out, 0)
                io.output(v2.led, 1)
                io.output(v3.out, 0)
                io.output(v3.led, 1)
                io.output(v4.out, 0)
                io.output(v4.led, 1)
                time.sleep(1)

        # close the pressure lock off valve
        io.output(v0.out, 1)

        # if signal on output wait for the hold duration
        time.sleep(t)

        # make sure the input and output ports still have pressure after hold / no leaks 
        if io.input(S1.IN) == 1 and io.input(S2.IN) == 1:

            pr.append(p_check())
            print("Pressure at output after hold test = ", '{:.03f}'.format(pr[1]), "bar(g)")
            pressure_held = pr[1]
            bar_dif = pr[0] - pr[1]

            #check difference is within a tollerence of acceptability
            if pr[1] / pr[0] <0.9 :
                print("More than 10 percent of the pressure has been lost, review the leak tightness of the assembly") 
                er += 1
                c.execute("UPDATE Holdtest SET hold_test_Pass=?, Pressure_held=?, Pressure_dif=?, error=?", ("Fail", pressure_held, bar_dif,er))
                conn.commit()
                return False, er
            else:            

                c.execute("UPDATE Holdtest SET hold_test_Pass=?, Pressure_held=?, Pressure_dif=?", ("Pass", pressure_held, bar_dif))
                c.execute("UPDATE overview SET hold_test_Pass=?", ("Pass",))
                conn.commit()

                print("\nthe hold test is complete. over", hold_duration, "seconds", '{0:.3f}'.format(bar_dif),
                      "bar was lost, which is deemed acceptable.")

                # open the lock off valve ready for the cycle test
                io.output(v0.out, 0)
                return True, er

        elif io.input(S1.IN) == 1 and io.input(S2.IN) == 0:
            io.output(S2.led, 0)
            er += 1
            print("Prerssure lost ove the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]
            c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_Count=?,end_date=?",
                      ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", er, time_stamp))

            conn.commit()

            # De-energise all 4 coils
            input("press enter to close save and close the test")

            io.output(v1.out, 1)
            io.output(v1.led, 0)
            io.output(v2.out, 1)
            io.output(v2.led, 0)
            io.output(v3.out, 1)
            io.output(v3.led, 0)
            io.output(v4.out, 1)
            io.output(v4.led, 0)

            return False, er
    else:
        io.output(S1.led, 0)
        er += 1
        print("No pressure found at input, remove the test box cover and check the hold valve..")
        errorLog.append(datetime.datetime.now())

        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]
        c.execute("UPDATE overview SET hold_test_Pass=?,cycle_test_Pass=?,notes=?,error_count=?,end_date=?",
                  ("Fail", "Fail", "Pressure lost over the hold duration check for leaks", er, time_stamp))

        conn.commit()

        input("press enter to close save and close the test")
        # De-energise all 4 coils
        io.output(v1.out, 1)
        io.output(v1.led, 0)
        io.output(v2.out, 1)
        io.output(v2.led, 0)
        io.output(v3.out, 1)
        io.output(v3.led, 0)
        io.output(v4.out, 1)
        io.output(v4.led, 0)

        return False, er


# main program
try:
    tester = input("Please enter your name or ID: ")
    test_ID = input("Please enter the test ID: ")
    part_code = input("Please enter the sample part code: ")
    
    Email = ""
    while Email == "" or Email[0] != "N" or Email[0] != "y":
        Email = input("would you like email reporting Y/N:").upper()

        if Email == "Y":
            receiver_email = str(input("what is your email address?:"))
            break
        elif Email == "N":
            break
        elif Email == "":
            print("Please enter Y/N:")

        else:
            print("Please enter Y/N:")

    hold_duration = hold_time()
    i_max = cycle_max()
    if Email == "Y":
        print("\nhi {},\nIf there is an error i'll try to reach you at {},\nThe hold test will run over {}s and will "
              "then perform {} cycles.".format(tester, receiver_email, hold_duration, i_max))
    else:
        print("\nhi {},\nYou have selected not to have email reporting.\nPlease check on the test periodically.\n"
              "The hold test will run over {}s and will then perform {} cycles.".format(tester, hold_duration, i_max))

    input("\nPress Enter to start the test")

    start = datetime.datetime.now()

    fileName = "/home/pi/RVM/varificationDatabase_files/%s.sqlite" % test_ID
    print("")
    print(fileName)
    print("")
    conn = sqlite3.connect(fileName)
    c = conn.cursor()

    # sqlite time_stamp
    c.execute("SELECT datetime('now','localtime')")
    time_stamp = c.fetchone()[0]

    if __name__ == '__main__':

        database = "/home/pi/RVM/Database_files/%s.db" % test_ID

        table_create_overview = '''CREATE TABLE IF NOT EXISTS overview (
                        id integer PRIMARY KEY,
                        tester_ID text ,
                        Serial_ID text ,
                        part_code text ,
                        test_date text ,
                        end_date text ,
                        hold_test_Pass text ,
                        cycle_test_Pass text,
                        error_count integer,
                        notes text
                        )'''

        table_create_Cycletest = '''CREATE TABLE IF NOT EXISTS Cycletest (
                        cycle_number integer PRIMARY KEY,
                        cycle_start integer,
                        v1 text,
                        v2 text,
                        v3 text,
                        v4 text,
                        cycle_end integer,
                        error integer,
                        major_error integer,
                        cycle_test_Pass text,
                        notes text
                        )'''
        table_create_Holdtest = '''CREATE TABLE IF NOT EXISTS Holdtest(
                        id integer PRIMARY KEY,
                        Hold_start text,
                        Pressure_ref real,
                        hold_duration text,
                        Pressure_held real,
                        Pressure_dif real,
                        hold_test_Pass text,
                        error integer
                        )'''

        if conn is not None:

            """ create a table from the create_table_sql statement
            :param conn: Connection object
            :param create_table_sql: a CREATE TABLE statement
            :return:
            """
            c.execute(table_create_overview)
            c.execute(table_create_Cycletest)
            c.execute(table_create_Holdtest)

        else:
            print("Error! cannot create the database connection.")

        c.execute("INSERT INTO overview (tester_ID, part_code, Serial_ID, test_date, error_count) VALUES(?,?,?,?,?)",
                  (tester, part_code, test_ID, start, errorCount))

        conn.commit()

        # initialise cycle counter
        i = 1

        holdtest = hold_test(hold_duration, errorCount, switchTime, bar)
        print("error count is:", holdtest[1])
        errorCount = holdtest[1]

        testGo = holdtest[0]

        if not testGo:
            x = ""
            while x == "" or x[0] != "N" or x[0] != "Y":
                x = input("The hold test failed, would you like to carry on with the cycle testing (Y) or save and "
                          "close the test (N)? Please enter Y/N:").upper()
                if x == "Y":
                    testGo = True
                    break
                elif x == "N":
                    raise KeyboardInterrupt

                elif x == "":
                    print("Please enter Y/N:")

                else:
                    print("Please enter Y/N:")

        outputOn = io.input(18)

        while i <= i_max:

            if not testGo:

                errorCount += 1
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute(
                    "UPDATE Cycletest SET error=?, notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                    (errorCount, "input pressure lost- Test Paused"))
                c.execute("UPDATE overview SET error_count=?,notes=?",(errorCount, "input pressure lost- Test Paused"))
                conn.commit()

                while io.input(S1.IN) == 0:
                    time.sleep(.5)
                    testGo = io.input(S1.IN)

            elif not outputOn:

                c.execute("UPDATE Cycletest SET notes=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM ""Cycletest)", 
                        ("no pressure registered at output- Test failed",))

                c.execute("UPDATE overview SET cycle_test_Pass=?, notes=?, end_date=?",
                        ("Fail", "no pressure registered at output- Test failed", time_stamp))
                conn.commit()

                if Email == "Y":
                    error_email.erroremail(smtp_server, port, sender_email, password, receiver_email)
                else:
                    pass
                print("The output has been lost, This shouldnt have happened and is a test Failure")
                raise KeyboardInterrupt

                #input("The output has been lost, Major error logged Press Enter to continue with test...")

                #if not outputOn:
                #    outputOn = True

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            c.execute("INSERT INTO Cycletest (cycle_start) VALUES(?)", (time_stamp,))

            for x in cyclelist:
                # v# turns off
                io.output(x.out, 1)
                io.output(x.led, 0)
                time.sleep(switchTime)
                # v# turns on
                io.output(x.out, 0)
                io.output(x.led, 1)
                time.sleep(switchTime)
                # check for S1
                testGo = io.input(S1.IN)
                io.output(S1.led, testGo)

                # check for S2 ==1 - if input ==1  but output == 0 there is major error
                outputOn = io.input(S2.IN)
                io.output(S2.led, outputOn)

                if not outputOn:
                    major_error +=1
                    c.execute("SELECT datetime('now','localtime')")
                    time_stamp = c.fetchone()[0]

                    if x.name == "v1":
                        c.execute("UPDATE Cycletest SET v1 = ?, major_error = ?, cycle_end = ? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                                 ("Fail",major_error,time_stamp))
                    elif x.name == "v2":
                        c.execute("UPDATE Cycletest SET v2 = ?, major_error = ?, cycle_end = ? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                                 ("Fail",major_error,time_stamp))
                    elif x.name == "v3":
                        c.execute("UPDATE Cycletest SET v3 = ?, major_error = ?, cycle_end = ? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                                 ("Fail",major_error,time_stamp))
                    elif x.name == "v4":
                        c.execute("UPDATE Cycletest SET v4=?, major_error = ?, cycle_end = ? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                                 ("Fail",major_error,time_stamp))

                if x.name == "v1":
                    c.execute("UPDATE Cycletest SET v1=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                              ("Pass",))
                elif x.name == "v2":
                    c.execute("UPDATE Cycletest SET v2=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                              ("Pass",))
                elif x.name == "v3":
                    c.execute("UPDATE Cycletest SET v3=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                              ("Pass",))
                elif x.name == "v4":
                    c.execute("UPDATE Cycletest SET v4=? WHERE cycle_number=(SELECT MAX(cycle_number)FROM Cycletest)",
                              ("Pass",))

            # sqlite time_stamp
            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            c.execute("UPDATE Cycletest SET cycle_end=? WHERE cycle_number=(SELECT MAX(cycle_number) FROM Cycletest)",
                      (time_stamp,))
            c.execute("UPDATE overview SET error_count=?",(errorCount,))
            conn.commit()

            # add one to the cycle counter
            i += 1

        io.output(v0.out, 1)
        end = datetime.datetime.now()

        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]

        c.execute("UPDATE overview SET cycle_test_Pass=?,end_date=?", ("Pass", time_stamp))
        conn.commit()

        print(end - start)

        if not errorLog:
            print("No Errors Occurred")
        else:
            print(errorLog)
        conn.close()
        
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

        open_data(fileName)

# what happens when you hit ctl-c
except KeyboardInterrupt:
    print("test ended")
    print('\n', "cycles completed = ", i)

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
