#!/usr/bin/env python
# coding: utf-8

import sqlite3
from sqlite3 import Error
import RPi.GPIO as io 
import os
import time, datetime

#setup pins 
io.setmode(io.BCM) 

#set pins for output
io.setup(14,io.OUT)
io.setup(15,io.OUT)
io.setup(26,io.OUT)
io.setup(27,io.OUT)

#set pins for input
io.setup(17, io.IN, pull_up_down=io.PUD_DOWN)

#set outputs pin position 0/1
io.output(14,1)
io.output(15,1)
io.output(26,1)
io.output(27,1)


#set global variables
testGo=False
testIn={}
i=0
switchTime=0.25
pauseLog=[""]

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

def main(start):
    database = "/home/pi/RVM/Database_files/%s.db" %start
 
    sql_create_projects_table = """ CREATE TABLE IF NOT EXISTS testOverview (
                                        id integer PRIMARY KEY,
                                        name text NOT NULL,
                                        begin_date text,
                                        end_date text
                                    ); """
 
    sql_create_tasks_table = """CREATE TABLE IF NOT EXISTS testData (
                                    id integer PRIMARY KEY,
                                    name text NOT NULL,
                                    priority integer,
                                    status_id integer NOT NULL,
                                    project_id integer NOT NULL,
                                    begin_date text NOT NULL,
                                    end_date text NOT NULL,
                                    FOREIGN KEY (project_id) REFERENCES projects (id)
                                );"""
       # create a database connection
    conn = create_connection(database)
    if conn is not None:
        # create projects table
        create_table(conn, sql_create_projects_table)
        # create tasks table
        create_table(conn, sql_create_tasks_table)
    else:
        print("Error! cannot create the database connection.")


def holdTest(hold_duration):
	"""
	check for a pressure input signal using microswitches 
	"""

	if io.input(17)==1:
		#energise all 4 coils
		io.output(14,0)
		io.output(15,0)
		io.output(26,0)
		io.output(27,0)
		#wait for the hold duration
		time.sleep(hold_duration)
		if io.input(17)==1:
			return True
		else: 
			print("Pressure at Input lost over the hold duration- Pressure hold test failed")
			#De-energise all 4 coils
			io.output(14,1)
			io.output(15,1)
			io.output(26,1)
			io.output(27,1)	
			raise KeyboardInterrupt
					
			return False
	else:	

		print("No pressure found at input, Please start again.")
		#De-energise all 4 coils
		io.output(14,1)
		io.output(15,1)
		io.output(26,1)
		io.output(27,1)	
		raise KeyboardInterrupt

#main programd

try:

	#update time as SqLite3 uderstands it
	#c.execute("SELECT datetime('now','localtime')")
	#timestamp=c.fetchone()[0]

	
	tester = input("please enter your name or ID:")	
	hold_days=-1
	while not hold_days in range(0,365,1):
		try:
			hold_days = int(input("please enter how many days to hold test for (0-365):"))
		except ValueError:
			print("Enter a number between 0 and 365")

	
	hold_hrs=-1
	while not hold_hrs in range(0,24,1):
		try:
			hold_hrs = int(input("please enter how many hours to hold test for (0-24):"))
		except ValueError:
			print("Enter a number between 0 and 24")
	
	hold_min=-1
	while not hold_min in range(0,60,1):
		try:
			hold_min = int(input("please enter how many minutes to hold test for (0-60):"))
		except ValueError:
			print("Enter a number between 0 and 60")
	
	hold_sec=-1
	while not hold_sec in range(0,60,1):
		try:
			hold_sec = int(input("please enter how many seconds to hold test for (0-60):"))
		except ValueError:
			print("Enter a number between 0 and 60")
	
	i_max=-1
	while not i_max in range(1,10000000,1):
		try:
			i_max = int(input("lease enter how many cycles to run (1-10,000,000):"))
		except ValueError:
			print("Enter a number between 1 and 10,000,000")
	

	hold_duration = (hold_sec)+(hold_min*60)+(hold_hrs*3600)+(hold_days*24*3600)
	
	testIn={"hold_days":hold_days,"hold_hrs":hold_hrs,"hold_min":hold_min,"hold_sec":hold_sec,"i_max":i_max}
	
	print(tester)
	
	print(testIn)
		
	input("Press Enter to start the test")

	start = datetime.datetime.now()


	fileName="/home/pi/RVM/Database_files/%s" %start
	print(fileName)

	#initialise counter
	i=0
	
	conn=sqlite3.connect(fileName)

	if __name__ == '__main__':
    main(start)
		
	testGo=holdTest(hold_duration)

	i+=1
		 
	while i <= i_max:
		if testGo==False:
			pauseLog.append(datetime.datetime.now())	
			while io.input(17)==0:		
				time.sleep(0.5)
				testGo=io.input(17)
			pauseLog.append(datetime.datetime.now())	
		else:
			#v1 turns off
			io.output(14,1)
			time.sleep(switchTime)
			#v1 turns on
			io.output(14,0)

			#v2 turns off
			io.output(15,1)
			time.sleep(switchTime)
			#V2 turns on
			io.output(15,0)

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


#what happens when you hit ctl-c
except KeyboardInterrupt:
	print('\n', i)

#cleanup
finally:
	io.cleanup()
	conn.close()
	end = datetime.datetime.now()
	print(end - start)
	if pauseLog == [""]:
		print("No Errors Occured")
	else:
		print(pauseLog)

