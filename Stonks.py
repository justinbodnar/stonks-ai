####################
# Stonks.py        #
# by Justin Bodnar #
####################
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import yfinance as yf
import pickle
import random
import time
import signal
import linecache
import sys
import tensorflow as tf
import keras
import numpy as np
import os

# helper class to suppress random errors
class DevNull:
	def write(self, msg):
		pass

# set stderr to redirect to helper class
sys.stderr = DevNull()

# PrintException() funct
# to print a more verbose error message
def PrintException():

	exc_type, exc_obj, tb = sys.exc_info()
	f = tb.tb_frame
	lineno = tb.tb_lineno
	filename = f.f_code.co_filename
	linecache.checkcache(filename)
	line = linecache.getline(filename, lineno, f.f_globals)
	print( 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj) )


# global stock list
#stocks = [ "ACB", "F", "GE", "MSFT", "GPRO", "FIT", "AAPL", "PLUG", "AMD","SNAP", "CRON", "CGC", "TSLA", "FB", "BABA", "CHK", "UBER", "ZNGA", "NIO", "TWTR", "BAC", "AMZN", "T", "APHA", "RAD", "SBUX", "NVDA", "NFLX", "SPCE", "VSLR", "SQ", "KO" ] 
stocks = []
f = open("stonks.txt","r")
for line in f:
	stocks.append(line.strip())

# nDaysBefore() funct
# takes as input n, and a datestamp in format YYYY-MMM-DDD
# returns datestamp n days before
def nDaysBefore( n, d ):

	d = datetime.strptime(d[2:],"%y-%m-%d")
	d = d - timedelta(days=n-1)
	d = str(d)[:10]

	# return datestamp
	return d

# signal_handler() funct
def signal_handler(sgnum, frame):
	raise Exception("Timed out!")

# random_dates() funct
# format: YYYY-MM-DD
def random_dates():

	# grab a random month
	m = random.randrange(12)

	# determine how many days are in the random month
	if m == 1:
		d = 28
	elif m == 4:
		d = 29
	elif m ==0 or m == 6 or m == 7 or m == 11 or m == 2:
		d = 31
	elif m == 3 or m == 5 or m == 8 or m == 9 or m == 10:
		d = 30

	# grab a random year
	y = random.randrange(2009,2019)

	# casting as strings
	y = str(y)
	m += 1

	# padding months
	if m > 9:
		m = str(m)
	else:
		m = "0" + str(m)
	if d < 10:
		d = "0"+str(d)
	else:
		d = str(d)
	datestamp = y+"-"+m+"-"+d

	# start on second date
	# should be < 30 days per investment

	# inc month
	if int(m) == 12: # for christmas time investments i guess
		m = 1
		y = str( int(y)+1 )
	else:
		m = int(m)+1

	# padding month
	if m < 10:
		m = "0"+str(m)
	else:
		m = str(m)

	# random day
	d = random.randrange(27)+1

	# padding day
	if d < 9:
		d = "0"+str(d)
	else:
		d = str(d)

	# concat second datestamp string
	datestamp2 = y+"-"+m+"-"+d

	# return datestamps
	return datestamp, datestamp2

# get_stock_history() funct
# takes stock, level, n
# where stock is the stock to look at
# level is which data level to produce
# n is number of days in history to look at
# returns a datapoint of a 1D list
# uses yahoo finance api
def get_stock_history( stock, level, n ):

	print( "get_stock_function called" )

	# initial data_point and tag
	data_point = []

	# whole thing goes in a while loop until completed
	complete = False
	while not complete:

		# try-catch block
		try:

			history = yf.Ticker(stock).history(period=str(n)+"d")

			# get opening price
			open = float(history["Open"][0])

			# get closing price
			close = float(history["Close"][len(history)-1])

			# calculate percentage change
			change = close/open

			# level 0 requires the open/close chain structure, so start here
			level = int(level)
			if level == 0:

				# creating list of open/close requires casting as iterable list
				openhistory = []
				closehistory = []
				data_point = []
				for each in history["Open"]:
					openhistory.append(each)
				for each in history["Close"]:
					closehistory.append(each)
				for i in range( len(openhistory) ):
					data_point += [ np.float16(round(openhistory[i],2)), np.float(round(closehistory[i],2)) ]

				# if we made it this far, functions completed
				return data_point[(-2*n):]

			# if were level 1
			elif level is 1:

				# prepare lists
				data_point = []
				openhistory = []
				closehistory = []

				# grab each day in history
				for each in history["Open"]:
					openhistory.append(each)
				for each in history["Close"]:
					closehistory.append(each)

				# start caluclating percentages
				counter = 0
				lastclose = 0.0
				for each in openhistory:

					# cast each datum
					each = float(each)

					# hack for first element offset in calculating after market hours
					if counter < 1:
						counter = 1
						lastclose = closehistory[0]
						continue

					# calculate percent change from yesterdays close until todays open
					# %change = (new-old)*(100/old)
					change = ( each - lastclose ) * ( 100.0 / lastclose )
					data_point.append(change)
					lastclose = float(closehistory[counter])

					# calculate percent change from todays open until todays close
					# %change = (new-old)*(100/old)
					change = ( float(closehistory[counter]) - each ) * ( 100.0 / each )
					data_point.append( change )

					# increment counter
					counter += 1

				# if we made it this far, functions completed
				return data_point[(-2*n):]

			# if were level 2
			elif level is 2:
				print( "Level 2 TBA" )

		# just disregard errors
		except Exception as e:
			print
			print(e)
			PrintException()
			pass

	# return delta
	return data_point[(-n*2)+1:]

# random_investment() funct
# takes level, n, and d
# where level is which data level to produce
# n is number of days in history to look at
# d is number of days invested
# returns a datapoint of a 1D list
# uses yahoo finance api
# assumes bought at open price
# and sold at close price
def random_investment( level, n, d ):

	# initial data_point and tag
	data_point = []
	tag = -1

	# amount_invested is arbitrary
	amount_invested = 100.0

	# whole thing goes in a while loop until completed
	complete = False
	while not complete:

		# try-catch block
		try:

			# get random stock from global list of stocks to train on
			stock = stocks[random.randrange(len(stocks))]

			# output
			print( "Stock chosen:", stock )

			# start timer to catch infinite loops in yf class
			signal.signal(signal.SIGALRM, signal_handler)
			signal.alarm(15) # in seconds

			# get random date
			date_bought, date_sold = random_dates()

			# make the date_bought n days before date_sold
			date_bought = nDaysBefore( d, date_sold )

			# get the delta from yahoo finace api
			data = yf.download( stock, date_bought, date_sold )

			# get opening price
			open = float(data["Open"][date_bought])

			# get closing price
			close = float(data["Close"][date_sold])

			# calculate percentage change
			change = close/open

			# calculate sold price
			sold = amount_invested * change

			# calculate tag from delta
			delta = sold - amount_invested
			tag = delta > 0

			# get n days of history
			historyStopDatestamp = nDaysBefore( 2, date_bought)
			historyStartDatestamp = nDaysBefore( n, date_bought )
			history = yf.download(stock, historyStartDatestamp, nDaysBefore( 1, date_bought ) )

			# level 0 requires the open/close chain structure, so start here
			level = int(level)
			if level == 0:

				# creating list of open/close requires casting as iterable list
				openhistory = []
				closehistory = []
				data_point = []
				for each in history["Open"]:
					openhistory.append(each)
				for each in history["Close"]:
					closehistory.append(each)
				for i in range( len(openhistory) ):
					data_point += [ np.float16(round(openhistory[i],2)), np.float(round(closehistory[i],2)) ]

				# if we made it this far, functions completed
				return data_point[(-2*n):], tag

			# if were level 1
			elif level is 1:

				# prepare lists
				data_point = []
				openhistory = []
				closehistory = []

				# grab each day in history
				for each in history["Open"]:
					openhistory.append(each)
				for each in history["Close"]:
					closehistory.append(each)

				# start caluclating percentages
				counter = 0
				lastclose = 0.0
				for each in openhistory:

					# cast each datum
					each = float(each)

					# hack for first element offset in calculating after market hours
					if counter < 1:
						counter = 1
						lastclose = closehistory[0]
						continue

					# calculate percent change from yesterdays close until todays open
					# %change = (new-old)*(100/old)
					change = ( each - lastclose ) * ( 100.0 / lastclose )
					data_point.append(change)
					lastclose = float(closehistory[counter])

					# calculate percent change from todays open until todays close
					# %change = (new-old)*(100/old)
					change = ( float(closehistory[counter]) - each ) * ( 100.0 / each )
					data_point.append( change )

					# increment counter
					counter += 1

				# if we made it this far, functions completed
				return data_point[(-2*n):], tag

			# if were level 2
			elif level is 2:
				print( "Level 2 TBA" )

		# just disregard errors
		except Exception as e:
#			PrintException()
			pass

	# return delta
	return data_point[(-n*2)+1:], tag

# random_investment2() funct
# same as original random_investment() funct
# with improved functionality
def random_investment( level, n, d ):

	# initial data_point and tag
	data_point = []
	tag = -1

	# amount_invested is arbitrary
	amount_invested = 100.0

	# whole thing goes in a while loop until completed
	complete = False
	while not complete:

		# try-catch block
		try:

			# get random stock from global list of stocks to train on
			stock = stocks[random.randrange(len(stocks))]

			# output
			print( "Stock chosen:", stock )

			# start timer to catch infinite loops in yf class
			signal.signal(signal.SIGALRM, signal_handler)
			signal.alarm(15) # in seconds

			# get random date
			date_bought, date_sold = random_dates()

			# get the delta from yahoo finace api
			data = yf.Ticker(stock).history(period=str(d)+"d")

			# get opening price
			open = float(data["Open"][0])

			# get closing price
			close = float(data["Close"][len(data)-1])

			# calculate percentage change
			change = close/open

			# calculate sold price
			sold = amount_invested * change

			# calculate tag from delta
			delta = sold - amount_invested
			tag = delta > 0

			# get n days of history
			history = yf.Ticker(stock).history(period=str(n)+"d")

			# level 0 requires the open/close chain structure, so start here
			level = int(level)
			if level == 0:

				# creating list of open/close requires casting as iterable list
				openhistory = []
				closehistory = []
				data_point = []
				for each in history["Open"]:
					openhistory.append(each)
				for each in history["Close"]:
					closehistory.append(each)
				for i in range( len(openhistory) ):
					data_point += [ np.float16(round(openhistory[i],2)), np.float(round(closehistory[i],2)) ]

				# if we made it this far, functions completed
				return data_point[(-2*n):], tag

			# if were level 1
			elif level is 1:

				# prepare lists
				data_point = []
				openhistory = []
				closehistory = []

				# grab each day in history
				for each in history["Open"]:
					openhistory.append(each)
				for each in history["Close"]:
					closehistory.append(each)

				# start caluclating percentages
				counter = 0
				lastclose = 0.0
				for each in openhistory:

					# cast each datum
					each = float(each)

					# hack for first element offset in calculating after market hours
					if counter < 1:
						counter = 1
						lastclose = closehistory[0]
						continue

					# calculate percent change from yesterdays close until todays open
					# %change = (new-old)*(100/old)
					change = ( each - lastclose ) * ( 100.0 / lastclose )
					data_point.append(change)
					lastclose = float(closehistory[counter])

					# calculate percent change from todays open until todays close
					# %change = (new-old)*(100/old)
					change = ( float(closehistory[counter]) - each ) * ( 100.0 / each )
					data_point.append( change )

					# increment counter
					counter += 1

				# if we made it this far, functions completed
				return data_point[(-2*n):], tag

			# if were level 2
			elif level is 2:
				print( "Level 2 TBA" )

		# just disregard errors
		except Exception as e:
#			PrintException()
			pass

	# return delta
	return data_point[(-n*2)+1:], tag


# createDataSet() funct
# uses random_investment function
# level number of data level
# size is the size of dataset
# n number of days to look at historically before investing
# d number of days to stay invested
# and n is number of days in history to look at
# returns 2 lists: data, tags
def createDataSet(level, size, n, d):

	# setup vars
	data = []
	tags = []

	# lets get a few random trades and see how we make out
	# each investment will be $100.00
	i = 0
	while len(data) < size:

		# print output
		print( "[", i+1, "of", size, "]" )
		i = i + 1

		# try to extract a random data point
		try:
			data_point, tag = random_investment( level, n, d )
			data.append( data_point )
			tags.append( tag )

		# catch exception
		except Exception as e:

			# do nothing
#			PrintException()
			pass

	# return the data and tags lists
	return data, tags


###############
# main method #
###############
def main():

	# clear the screen
	for i in range(30):
		print()

	# print opening header
	print( "##########################" )
	print( "Stonks.py by Justin Bodnar" )
	print()
	print( "Can we teach computers to speculate?" )
	print()

	# main program infinite loop
	choice = 420
	while choice > 0:

		# main menu text
		print()
		print( "Menu" )
		print( "1. Create new data sets" )
		print( "2. Extend data set" )
		print( "3. List and analyze available data sets" )
		print( "4. Train a model on a data set" )
		print( "5. Grab and view example datum" )

		# get user chice
		choice = int(input( "\nEnter choice: "))

		# create new data set
		if choice == 1:

			# get user parameters
			print( "Filename: level-sizeOfDataset-daysOfHistory-daysInvested_[data|tags]" )
			level = int(input("Enter data level: "))
			sizeOfDataset = int(input("Enter size of dataset: "))
			daysOfHistory = int(input("Enter the number of days to look at: "))
			daysInvested = int(input("Enter number of days invested: "))
			filename = str(level)+"-"+str(sizeOfDataset)+"-"+str(daysOfHistory)+"-"+str(daysInvested)
			# create data set
			data, tags = createDataSet(level, sizeOfDataset, daysOfHistory, daysInvested)

			# save data sets
			try:
				pickle.dump( data, open( "./datasets/"+filename+"_data", "wb" ) )
				pickle.dump( tags, open ( "./datasets/"+filename+"_tags", "wb" ) )
			except Exception as e:
				print( "error on data or tag save" )
#				PrintException()

			print( "Dataset saved as ./datasets/", filename+"_tags and ./datasets/", filename+"_data" ) 
			print( "Filename: level-sizeOfDataset-daysOfHistory-daysInvested_[data|tags]" )
			# wait f or user  input
			pause = input( "Press enter to continue" )

		# extend a data set
		elif choice == 2:

			# try-catch block
			try:
				print( "Available data sets" )
				# list files in datalist dir
				for file in os.listdir("./datasets"):
					# only look at dataset files
					if "data" not in file:
						continue
					else:
						print( file )
				print( "\nFilename: level-sizeOfDataset-daysOfHistory-daysInvested_[data|tags]" )
				level = int(input("Enter data level: "))
				sizeOfNewDataset = int(input("Enter number of new data points: "))
				daysOfHistory = int(input("Enter the number of days to look at: "))
				daysInvested = int(input("Enter number of days invested: "))

				# unpickle lists
				data = pickle.load( open( "./datasets/"+file+"_data", "rb" ) )
				tags = pickle.load( open( "./datasets/"+file+"_tags", "rb" ) )

				# get new list
				newData, newTags = createDataSet(level, sizeOfNewDataset, daysOfHistory, daysInvested)

				# append lists
				data += newData
				tags += newTags

				# repickle list
				pickle.dump( data, open( "./datasets/"+file+"_data", "wb" ) )
				pickle.dump( tags, open( "./datasets/"+file+"_tags", "wb" ) )

			# catch exceptions
			except Exceptions as e:

#				PrintExceptions()
				pass

		# choice == 3
		# analyze available data sets
		elif choice == 3:

			# print header
			print()
			print("\nDatasets available:")

			# list files in datalist dir
			for file in os.listdir("./datasets"):

				# only look at dataset files
				if "data" not in file:
					continue

				# try to unpickle dataset file
				try:
					# unpickle
					data_set = pickle.load( open( "./datasets/"+file, "rb" ) )

					# get length of dim 2
					min = 99999999
					max = -1

					# loop through dim 1, checking each entry alonog dim 2 for size
					for data_point in data_set:

						# check for min or max
						if len(data_point) > max:
							max = len(data_point)
						if len(data_point) < min:
							min = len(data_point)
					# print output
					print()
					print( "Name: ", file )
					print( "Dim 1:", len(data_set) )
					if min == max:
						print( "Dim 2:", min )
					else:
						print( "Data set irregular with bounds (", min, ",", max, ")" )
						print( "Fixing with lower bound", min, "as new dim2 size" )

						# loop through dim 1, creating new dataset of proper dim 2 size
						regularized_data_set = []
						for data_point in data_set:
							regularized_data_set.append( data_point[-min:] )

						# replace the old dataset with the regularized one
						data_set = regularized_data_set

						# get new stats
						min = 999999
						max = -1
						# for each data_point
						for data_point in data_set:
							# check for new min or max
							if len(data_point) < min:
								min = len(data_point)
							if len(data_point) > max:
								max = len(data_point)

						# print new datset stats
						if min == max:
							print( "New dim 2:", min )
							print( "Repickling. Please rerun this function to confirm updates" )
							pickle.dump( data_set, open( "./datasets/"+file, "wb" ) )
						else:
							print( "Data set STILL irregular with bounds (", min, ",", max, ")" )

				# catch exception
				except Exception as e:

#					PrintException()
					pass

			print( "\nFilename: level-sizeOfDataset-daysOfHistory-daysInvested_[data|tags]" )
			# print newline for pretty output
			print()

			# wait for user to press enter
			pause = input( "Press enter to continue." )

		# choice 4
		# build model from data set
		elif choice == 4:

			# try to unpickle data set and train classifier
			try:
				print( "\nAvailable data sets" )
				# list files in datalist dir
				for file in os.listdir("./datasets"):
					# only look at dataset files
					if "data" not in file:
						 continue
					else:
						print( file )
				print( "\nFilename: level-sizeOfDataset-daysOfHistory-daysInvested_[data|tags]\n" )

				# get user parameters
				filename = input("Enter name of dataset: ")
				print( "Using 3-layer neural network" )
				epochs = int(input("Enter number of epochs: "))
				layer1 = int(input("Enter number of nodes for Layer 1: "))
				layer2 = int(input("Enter number of nodes for Layer 2: "))
				layer3 = int(input("Enter number of nodes for Layer 3: "))

				# unpickle the data and tags lists
				tags = pickle.load( open( "./datasets/"+filename+"_tags", "rb" ) )
				data = pickle.load( open( "./datasets/"+filename+"_data", "rb" ) )

				print("tags initial size:", len(tags))
				print("data initial size:", len(data))

				size = int( len(data)*(0.75) )

				train_data = np.array( data[1:size] )
				train_tags = np.array( tags[1:size] )
				test_data = np.array( data[size:] )
				test_tags = np.array( tags[size:] )


				print("tags training size:", len(train_tags))
				print("data training size:", len(train_data))
				print("tags testing size:", len(test_tags))
				print("data testing size:", len(test_data))


				model = keras.Sequential()
				model.add( keras.layers.Dense( layer1, input_dim=len(data[0]) ) )
				model.add( keras.layers.Dense( layer2, input_dim=26 ) )
				model.add( keras.layers.Dense( layer3, input_dim=13 ) )
				model.add( keras.layers.Dense(2, activation=tf.nn.softmax) )

				model.compile(optimizer='adam',loss='sparse_categorical_crossentropy',metrics=['accuracy'])

				model.fit(train_data, train_tags, epochs=epochs)

				test_loss, test_acc = model.evaluate(test_data, test_tags)

				print('Test accuracy:', test_acc)


				print( "Save model? Y or N" )
				choice = input( "\nEnter choice: ")

				if choice is "Y" or choice is "y":
					# save model
					model_json = model.to_json()
					with open( "models/stonk_model.json", "w") as json_file:
						json_file.write(model_json)
					# serialize weights to HDF5
					model.save_weights("models/stonk_model.h5")
					print( "Model saved" )


			# catch exceptions
			except Exception as e:

				# print error
				PrintException()

				# do nothing
				pass

			# pause for user input
			pause = input( "Press enter to continue" )
		# grab and view datum
		elif choice == 5:
			level = int(input("Enter data level: "))
			stock = input("Enter stock to grab: ")
			n = int(input("Enter number of days to look back at: "))
			datum = get_stock_history( stock, level, n )
			print( datum )
		# choice != VALID
		else:
			pause = input("Invalid choice\nPress enter to continue.")
main()

