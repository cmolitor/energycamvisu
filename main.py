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
def getData(user, password, uuid):
	global oldValue

	[apiConnection, headers] = connectQloud(user, password)

	if apiConnection == 1:
		print "Could not connect to server. Something went wrong."
		exit()

	# here hard coded sensor; todo: scan for sensor uuid in previous response and put uuid in the following request
	#apiConnection.request("GET", "/api/sensor/b96f86c0-245a-11e7-a2db-00259075ae2a", headers=headers)
	#response = json.loads(apiConnection.getresponse().read())
	#print "sensor data: " + str(response)


	#body = json.dumps({"from": "1499280198","to": "1499366598"})
	#print body

	apiConnection.request("GET", "/api/sensor/b96f86c0-245a-11e7-a2db-00259075ae2a/data?from=1499280198&to=1499366598&count=96", headers=headers)
	response = json.loads(apiConnection.getresponse().read())
	print "sensor data: " + str(response)
	for key in response['data'].keys():
		print int(int(key)/1000)

	newValue = response['sensor']['state']['data'][1]
	measTime = response['sensor']['recv_time']

	# print "Data: " + str(newValue) + " Time stamp: " + str(measTime)

	#now = datetime.now()
	lastMeasTime = datetime.fromtimestamp(measTime)

	if oldValue != 0:
		# print "Another round."
		deltaValue = newValue - oldValue[1]
		deltaTime = (lastMeasTime - oldValue[0]).total_seconds()

		# print "intermediate values: " + str(deltaValue) + " " + str(deltaTime)

		if deltaValue > 0:
			print "Detected a difference between old and new value."
			powerValue = float(deltaValue)/float(deltaTime)
			print "Zeit: " + str(lastMeasTime) + "Leistung: " + str(powerValue)

			# Werte Speichern
			print "Jetzt neue Werte speichern"
			oldValue = [lastMeasTime, newValue]
			print str(oldValue)

	else:
		print "Initial values stored."
		oldValue = [lastMeasTime, newValue]
		print oldValue

	apiConnection.request("DELETE", "/api/session", headers=headers)

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


	while(1):
		getData(user, password, uuid1)
		time.sleep(10)

	# Start the scheduler
	# sched = BlockingScheduler()

	# sched.add_job(lambda: getData(apiConnection, header, uuid1), 'interval', seconds=int(60))
	# sched.start()
