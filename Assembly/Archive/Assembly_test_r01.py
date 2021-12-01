#!/usr/bin/env python
# coding: utf-8
# r04 - fully working test script, messy sql database

import datetime
import sqlite3
import subprocess
import time
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
i = 0
i_max = 50
hold_duration = 60
switchTime = 0.3
bar = []
errorLog = []
errorCount = 0
major_error = 0
cyclelist = [v1, v2, v3, v4]
Scenario_cycle = 0
Scenario_cycle_max=5
Scenario_dict = {"1": [v1, v2], "2": [v1, v3], "3": [v1, v4], "4": [v2, v3], "5": [v2, v4],
                 "6": [v3, v4]}


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

def hold_test(t, er, s, pr):
    """
    check for a pressure input signal using micro-switches

    t = hold_duration as time in seconds
    er = error count
    s = switch time

    """
    c.execute("SELECT datetime('now','localtime')")
    holdtest_start = c.fetchone()[0]
    c.execute("INSERT INTO Hold_test(Hold_start, Hold_duration, Error) VALUES(?,?,?)",(holdtest_start, hold_duration, er))
    conn.commit()

    if io.input(S0.IN) == 1:
        io.output(v0.out, 0)
        time.sleep(s)
    else:
        while io.input(S0.IN) == 0:
            er += 1
            noIn = input("No mains air available - check the supply and enter Y to try again or 'N' to close the test") 

            while noIn == False:
                noIN = input("No mains air available - check the supply and enter 'Y' to try again or 'N' to close the test") 

                if noIn[0].upper() == "N":
                
                    c.execute("UPDATE Hold_test SET hold_test_Pass=?, Pressure_ref=?, hold_duration=?, Pressure_held=?, Pressure_dif=?, Error=?", ("Fail", 0, 0, 0, 0, er))
                    c.execute("UPDATE Overview set hold_test_Pass=? Error_count=?", ("Fail", er))
                    conn.commit()
                   
                    return False, er

            else:
                break

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
        c.execute("UPDATE Hold_test SET Pressure_ref=?", (pr[0],))
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
                time.sleep(.5)

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
                er += 1
                print("More than 10 percent of the pressure has been lost, review the leak tightness of the assembly") 
                

                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute("UPDATE Hold_test SET Hold_test_Pass=?, Pressure_held=?, Pressure_dif=?, Error=?",
                    ("Fail", pressure_held, bar_dif, er))
                c.execute("UPDATE Overview SET Hold_test_Pass=?, Error_count=?, Notes=?, End_date=?", ("Fail", er, "leakage is outside acceptable range",time_stamp))
                conn.commit()
                return False, er
            else:            

                c.execute("UPDATE Hold_test SET Hold_test_Pass=?, Pressure_held=?, Pressure_dif=?", ("Pass", pressure_held, bar_dif))
                c.execute("UPDATE Overview SET Hold_test_Pass=?", ("Pass",))
                conn.commit()

                print("\nthe hold test is complete. over", hold_duration, "seconds", '{0:.3f}'.format(bar_dif),
                      "bar was lost, which is deemed acceptable.")

                # open the lock off valve ready for the cycle test
                io.output(v0.out, 0)
                return True, er

        elif io.input(S1.IN) == 1 and io.input(S2.IN) == 0:
            io.output(S2.led, 0)
            er += 1
            print("Pressure lost ove the hold duration check for leaks - Pressure hold test failed")
            errorLog.append(datetime.datetime.now())

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]
            c.execute("UPDATE Overview SET Hold_test_Pass=?, Notes=?, Error_count=?, End_date=?",
                      ("Fail", "All Pressure lost over the hold duration check for major leaks", er, time_stamp))

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
        print("No pressure found at RVM input, remove the test box cover and check the hold valve..")

        errorLog.append(datetime.datetime.now())
        c.execute("SELECT datetime('now','localtime')")
        time_stamp = c.fetchone()[0]

        c.execute("UPDATE Overview SET Hold_test_Pass=?, Notes=?, Error_count=?, End_date=?",
                  ("Fail", "Pressure lost over the hold duration check for leaks", er, time_stamp))

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
    Sales_Order = input("Please enter the Sales order (either '1S#####' or 'SAMP####')")
    Serial = input("Please enter the Serial number: ")
    Part_code = input("Please enter the sample part code: ")
    print("\nHi {},"
          "\nThe hold test will run over {}s and will then perform {} cycles & 30 double failure Scenarios".format(tester, hold_duration, i_max))

    input("\nPress Enter to start the test")
    start = datetime.datetime.now()

    fileName = "/home/pi/RVM/Assembly/TestDB/%s.sqlite" % Serial
    print("\n","the Database is saved at: ",fileName,"\n")
    
    conn = sqlite3.connect(fileName)
    c = conn.cursor()

    # sqlite time_stamp
    c.execute("SELECT datetime('now','localtime')")
    time_stamp = c.fetchone()[0]

    if __name__ == '__main__':
        database = "/home/pi/RVM/Assembly/TestDB/%s.sqlite" % Serial

        table_create_Overview = '''CREATE TABLE IF NOT EXISTS Overview (
                        Test integer PRIMARY KEY,
                        Tester_ID text ,
                        Sales_Order text,
                        Serial_no text ,
                        Part_Code text ,
                        Test_date text ,
                        End_date text ,
                        Hold_test_Pass text ,
                        Cycle_test_Pass text,
                        Scenario_Test_Pass text,
                        Error_count integer,
                        Notes text
                        )'''

        table_create_Cycle_test = '''CREATE TABLE IF NOT EXISTS Cycle_test (
                        Cycle_number integer PRIMARY KEY,
                        Cycle_start integer,
                        v1 text,
                        v2 text,
                        v3 text,
                        v4 text,
                        Cycle_end integer,
                        Error integer,
                        Major_error integer,
                        Notes text
                        )'''
        table_create_Hold_test = '''CREATE TABLE IF NOT EXISTS Hold_test(
                        Test integer PRIMARY KEY,
                        Hold_start text,
                        Pressure_ref real,
                        Hold_duration text,
                        Pressure_held real,
                        Pressure_dif real,
                        Hold_test_Pass text,
                        Error integer
                        )'''
        table_create_Scenario_test = '''CREATE TABLE IF NOT EXISTS Scenario_test(
                        ID integer PRIMARY KEY,
                        Scenario integer,
                        Scenario_start text,
                        v1 text,
                        v2 text,
                        v3 text,
                        v4 text,
                        Scenario_result
                        Scenario_end integer,
                        Error integer,
                        Major_error integer,
                        Notes text
                        )'''

        if conn is not None:

            """ create a table from the create_table_sql statement
            :param conn: Connection object
            :param create_table_sql: a CREATE TABLE statement
            :return:
            """
            c.execute(table_create_Overview)
            c.execute(table_create_Cycle_test)
            c.execute(table_create_Hold_test)
            c.execute(table_create_Scenario_test)

        else:
            print("Error! cannot create the database connection.")

        c.execute("INSERT INTO Overview (Tester_ID, Part_code, Sales_Order, Serial_no, test_date, Error_count) VALUES(?,?,?,?,?,?)",
                  (tester, Part_code, Sales_Order, Serial, start, errorCount))

        conn.commit()

        # initialise cycle counter
        i = 1

        holdtest = hold_test(hold_duration, errorCount, switchTime, bar)

        errorCount = holdtest[1]

        testGo = holdtest[0]

        while not testGo:
            x = ""
            while x == "" or x[0] != "N" or x[0] != "Y":
                x = input("The hold test failed, would you like to carry on with the cycle testing (Y) or save and "
                          "close the test (N)? Please enter Y/N:").upper()
                if x == "Y":
                    testGo = True
                    io.output(v0.out, 0)
                    break
                elif x == "N":
                    raise KeyboardInterrupt

                elif x == "":
                    print("Please enter Y/N:")

                else:
                    print("Please enter Y/N:")

        outputOn = io.input(18)

        while i <= i_max:

            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            c.execute("INSERT INTO Cycle_test (Cycle_start, Error, Major_error) VALUES(?,?,?)", (time_stamp, errorCount, major_error))

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

                if not testGo:
                    errorCount += 1
                    errorLog.append(datetime.datetime.now())
                    c.execute("SELECT datetime('now','localtime')")

                    time_stamp = c.fetchone()[0]

                    c.execute(
                        "UPDATE Cycle_test SET Error=?, Notes=? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                        (errorCount, "input pressure lost - Test Paused"))
                    c.execute("UPDATE Overview SET Error_count=?, Notes=?",(errorCount, "input pressure lost- Test Paused"))
                    conn.commit()

                    while io.input(S1.IN) == 0:
                        time.sleep(.5)
                        testGo = io.input(S1.IN)

                # check for S2 ==1 - if input ==1  but output == 0 there is major error
                outputOn = io.input(S2.IN)
                io.output(S2.led, outputOn)

                if not outputOn:
                    major_error +=1
                    c.execute("SELECT datetime('now','localtime')")
                    time_stamp = c.fetchone()[0]

                    if x.name == "v1":
                        c.execute("UPDATE Cycle_test SET v1 = ?, Major_error = ?, Cycle_end = ? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                                 ("Fail", major_error, time_stamp))
                    elif x.name == "v2":
                        c.execute("UPDATE Cycle_test SET v2 = ?, Major_error = ?, Cycle_end = ? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                                 ("Fail", major_error, time_stamp))
                    elif x.name == "v3":
                        c.execute("UPDATE Cycle_test SET v3 = ?, Major_error = ?, Cycle_end = ? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                                 ("Fail", major_error, time_stamp))
                    elif x.name == "v4":
                        c.execute("UPDATE Cycle_test SET v4 = ?, Major_error = ?, Cycle_end = ? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                                 ("Fail", major_error, time_stamp))
                    else: 
                        pass

                    c.execute("UPDATE Overview SET Cycle_test_Pass=?, End_date=?, Error_count=?, Notes=?",
                        ("Fail", time_stamp, errorCount+major_error, "Output lost during cycle test"))
                    conn.commit()
                    print("Test failed - RVM lost the output during the cycle test")
                    raise KeyboardInterrupt


                if x.name == "v1":
                    c.execute("UPDATE Cycle_test SET v1=? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                              ("Pass",))
                elif x.name == "v2":
                    c.execute("UPDATE Cycle_test SET v2=? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                              ("Pass",))
                elif x.name == "v3":
                    c.execute("UPDATE Cycle_test SET v3=? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                              ("Pass",))
                elif x.name == "v4":
                    c.execute("UPDATE Cycle_test SET v4=? WHERE Cycle_number=(SELECT MAX(Cycle_number)FROM Cycle_test)",
                              ("Pass",))
    

            # sqlite time_stamp
            c.execute("SELECT datetime('now','localtime')")
            time_stamp = c.fetchone()[0]

            c.execute("UPDATE Cycle_test SET Cycle_end=? WHERE Cycle_number=(SELECT MAX(Cycle_number) FROM Cycle_test)",
                      (time_stamp,))
            c.execute("UPDATE Overview SET Error_count=?",(errorCount,))
            conn.commit()

            # add one to the cycle counter
            i += 1

        io.output(v0.out, 1)
        cycle_end = datetime.datetime.now()

        print("The cycle test lasted: ", cycle_end - start)
        c.execute("UPDATE Overview SET Cycle_test_Pass=?", ("Pass",))
        conn.commit()
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
            c.execute("SELECT datetime('now','localtime')")
            Scenario_start = c.fetchone()[0]
            c.execute("INSERT INTO Scenario_test (Scenario, Scenario_start, v1, v2, v3, v4, Scenario_result, Error,Major_error, Notes) VALUES(?,?,?,?,?,?,?,?,?,?)", (k, Scenario_start, "-", "-", "-", "-", "-", errorCount, major_error, "-"))
            
            for z in range (0,2):
                if x[z] == v1:
                    c.execute("UPDATE Scenario_test SET v1=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)",
                              ("OFF",))
                elif x[z] == v2:
                    c.execute("UPDATE Scenario_test SET v2=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)",
                              ("OFF",))
                elif x[z] == v3:
                    c.execute("UPDATE Scenario_test SET v3=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)",
                              ("OFF",))
                elif x[z] == v4:
                    c.execute("UPDATE Scenario_test SET v4=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)",
                              ("OFF",))
            conn.commit()
            
            # v# and LED# turns off
            io.output(x[0].out, 1)
            io.output(x[1].out, 1)
            io.output(x[0].led, 0)
            io.output(x[1].led, 0)
            time.sleep(switchTime)

            # check for S1
            testGo = io.input(S1.IN)
            io.output(S1.led, testGo)
            
            if not testGo:
                errorCount += 1
                errorLog.append(datetime.datetime.now())
                c.execute("SELECT datetime('now','localtime')")
                time_stamp = c.fetchone()[0]

                c.execute(
                    "UPDATE Scenario_test SET Error=?, Notes=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)",
                    (errorCount, "input pressure lost - Test Paused"))
                c.execute("UPDATE Overview SET Error_count=?, Notes=?",(errorCount, "input pressure lost- Test Paused"))

                conn.commit()

                while io.input(S1.IN) == 0:
                    time.sleep(.5)
                    testGo = io.input(S1.IN)
            
            # check for S2 ==1 - if input ==1  but output == 0 there is major error
            outputOn = io.input(S2.IN)
            io.output(S2.led, outputOn)

            if k == "1" or k == "4" or k == "6":
                if outputOn:
                    major_error+=1
                    c.execute("UPDATE Scenario_test SET Notes=?, Scenario_result=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)", 
                            ("pressure registered at output- Test failed", "Fail"))

                    c.execute("UPDATE Overview SET Scenario_Test_Pass=?, Notes=?, End_date=?",
                            ("Fail", "Scenario test- pressure registered at output- Test failed", time_stamp))
                    conn.commit()

                    print("An output has been found, This shouldnt have happened and indicates a leak path, is a test Failure")
                    raise KeyboardInterrupt
                else:
                    c.execute("UPDATE Scenario_test SET Scenario_result=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)", 
                             ("Pass",))


            elif k == "2" or k == "3" or k == "5":
                if not outputOn:
                    major_error+=1
                    c.execute("UPDATE Scenario_test SET notes=?, Scenario_result=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)", 
                            ("No pressure registered at output- Test failed", "Fail"))

                    c.execute("UPDATE overview SET Scenario_Test_Pass=?, notes=?, end_date=?",
                            ("Fail", "Scenario test- pressure registered at output- Test failed", time_stamp))
                    conn.commit()

                    print("The output has been lost, This shouldnt have happened and is a test Failure")
                    raise KeyboardInterrupt
                else:
                    c.execute("UPDATE Scenario_test SET Scenario_result=? WHERE ID=(SELECT MAX(ID)FROM Scenario_test)", 
                             ("Pass",))
                    # turn tested SOV back on
            io.output(x[0].out, 0)
            io.output(x[1].out, 0)
            io.output(x[0].led, 1)
            io.output(x[1].led, 1)
            time.sleep(switchTime)
            conn.commit()

        Scenario_cycle+=1

    c.execute("UPDATE Overview SET Scenario_Test_Pass=?",("Pass",))
    conn.commit()

####################################################################################
#end of testing

    end = datetime.datetime.now()
    c.execute("UPDATE Overview SET End_date=?",(end,))
    conn.commit()
    print("Testing time = ",end-start)

    if not errorLog:
            print("No Errors Occurred")
    else:
        print(errorLog)
        #conn.close()
# what happens when you hit ctl-c
except KeyboardInterrupt:
    print("test ended")
    print("\n", "Major errors ocured: ", major_error)
    print("\n", "minor errors ocured: ", errorCount)
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

    open_data(fileName)
    io.cleanup()
