# based on https://q-loud.de/api/example.html

import httplib
import json
import ConfigParser
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from influxdb import InfluxDBClient


oldValue = 0

# connect and login to server
def connectQloud(user, password):
	# get session information on api.cospace.de
	initialConnection = httplib.HTTPSConnection("api.cospace.de")
	initialConnection.request("GET", "/api/session")

	# result is JSON encoded
	response = json.loads(initialConnection.getresponse().read())

	# cut https:// prefix (7 characters) from server returned in JSON
	apiServer = response["server"][8:]

	# remember the session id
	sid = response["sid"]

	# create the connection for the following API requests
	apiConnection = httplib.HTTPSConnection(apiServer)

	# post credentials into session
	body = json.dumps({
	    "username": user,
	    "password": password
	})

	headers = {"Authorization": "Bearer " + sid}
	apiConnection.request("POST", "/api/session", body, headers=headers)
	response = json.loads(apiConnection.getresponse().read())
	# print "login response: " + str(response)

	if str(response['status']) != "ok":
		return 1

	return apiConnection, headers

# request data from server
def getData(apiConnection, headers, uuid):
	global oldValue
	# here hard coded sensor; todo: scan for sensor uuid in previous response and put uuid in the following request
	apiConnection.request("GET", "/api/sensor/b96f86c0-245a-11e7-a2db-00259075ae2a", headers=headers)
	response = json.loads(apiConnection.getresponse().read())
	#print "sensor data: " + str(response)

	newValue = response['sensor']['state']['data'][1]

	now = datetime.now()

	if oldValue != 0:
		deltaValue = newValue - oldValue[1]
		deltaTime = (oldValue[0] - now).total_seconds()

		if deltaValue > 0:
			powerValue = deltaValue/deltaTime
			print "Zeit: " + str(now) + "Leistung: " + powerValue

			# Werte Speichern
			oldValue = [now, newValue]

	else:
		print "Initial values stored."
		oldValue = [now, newValue]

# Main program
if __name__ == "__main__":
	print "====== Start Program ======="

	# Load data from config.ini
	config = ConfigParser.ConfigParser()
	config.readfp(open(r'config.ini'))
	# pushbullet token
	user = config.get('General', 'user')
	password = config.get('General', 'pass')

	uuid1 = config.get('Sensor1', 'uuid')

	[apiConnection, header] = connectQloud(user, password)

	if apiConnection == 1:
		print "Could not connect to server. Something went wrong."
		exit()

	# Start the scheduler
	sched = BlockingScheduler()

	sched.add_job(lambda: getData(apiConnection, header, uuid1), 'interval', seconds=int(60))
	sched.start()


