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
pauseLog=[]

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
						
			c.execute("UPDATE testData SET hold_test_results=?",("Passsed",))
		
			conn.commit()
			return True
		else: 
			print("Pressure at Input lost over the hold duration- Pressure hold test failed")
			pauseLog.append(datetime.datetime.now())
			c.execute("UPDATE testData SET hold_test_results=?,notes=?",("Failed","Pressure at Input lost over the hold duration- Pressure hold test failed"))
		
			conn.commit()
			#De-energise all 4 coils
			io.output(14,1)
			io.output(15,1)
			io.output(26,1)
			io.output(27,1)	
			raise KeyboardInterrupt
					
			return False
	else:	

		print("No pressure found at input, Please start again.")
		c.execute("UPDATE testData SET hold_test_results=?,notes=?",("Failed","No pressure found at input, Please start again."))
		
		conn.commit()
		#De-energise all 4 coils
		io.output(14,1)
		io.output(15,1)
		io.output(26,1)
		io.output(27,1)	
		raise KeyboardInterrupt
	

#main program

try:
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

		 
		while i <= i_max:
			if testGo==False:
				pauseLog.append(datetime.datetime.now())
				c.execute("SELECT datetime('now','localtime')")
				timeStamp=c.fetchone()[0]
				c.execute("INSERT INTO testData (error_time,cycle_no) VALUES(?,?)",(timeStamp,i))
				conn.commit()
				while io.input(17)==0:		
					time.sleep(0.5)
					testGo=io.input(17)
				pauseLog.append(datetime.datetime.now())
				c.execute("SELECT datetime('now','localtime')")
				timeStamp=c.fetchone()[0]
				c.execute("INSERT INTO testData (error_time) VALUES(?)",(timeStamp,))
				conn.commit()
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
				#sqlite timestamp
				c.execute("SELECT datetime('now','localtime')")
				timeStamp=c.fetchone()[0]
				c.execute("INSERT INTO testData (cycle_test_results,end_date,cycle_no) VALUES(?,?,?)",("Pass",timeStamp,i))
				conn.commit()


#what happens when you hit ctl-c
except KeyboardInterrupt:
	print('\n', i)
	print("test ended using keyboard interupt")
	fileName="/home/pi/RVM/Database_files/%s.sqlite" %start
	conn=sqlite3.connect(fileName)
	c=conn.cursor()
	#sqlite timestamp
	c.execute("SELECT datetime('now','localtime')")
	timeStamp=c.fetchone()[0]
	c.execute("INSERT INTO testData (notes,cycle_test_results,cycle_no,end_date) VALUES(?,?,?,?)",("Test ended before before completion","Failed",i,timeStamp))
	conn.commit()


#cleanup
finally:
	io.cleanup()
	print(start)
	fileName="/home/pi/RVM/Database_files/%s.sqlite" %start
	conn=sqlite3.connect(fileName)
	c=conn.cursor()
	#sqlite timestamp
	c.execute("SELECT datetime('now','localtime')")
	timeStamp=c.fetchone()[0]
	c.execute("INSERT INTO testData (name,test_setup_sec,test_setup_min,test_setup_hrs,test_setup_days,test_setup_imax,cycle_no,begin_date,end_date) VALUES(?,?,?,?,?,?,?,?,?)",(tester,hold_sec,hold_min,hold_hrs,hold_days,i_max,i,start,timeStamp))
	conn.commit()
	end = datetime.datetime.now()
	print(end - start)
	if pauseLog == []:
		print("No Errors Occured")
	else:
		print(pauseLog)
	conn.close()

