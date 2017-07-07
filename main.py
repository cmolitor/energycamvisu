# based on https://q-loud.de/api/example.html

import httplib
import json
import ConfigParser
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from influxdb import InfluxDBClient

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
def getData(user, password, uuid, starttime):
	# connect to qloud server
	[apiConnection, headers] = connectQloud(user, password)

	if apiConnection == 1:
		print "Could not connect to server. Something went wrong."
		exit()

	# request data from server
	values = list()
	#apiConnection.request("GET", "/api/sensor/b96f86c0-245a-11e7-a2db-00259075ae2a/data?from=" + starttime + "&to=1499366598&order=asc&count=50000", headers=headers)
	apiConnection.request("GET", "/api/sensor/b96f86c0-245a-11e7-a2db-00259075ae2a/data?from=" + starttime + "&count=50000", headers=headers)
	response = json.loads(apiConnection.getresponse().read())
	# print "sensor data: " + str(response)

	# extract data
	for key in response['data'].keys():
		#print int(int(key)/1000), response['data'][str(key)][1]
		values.append( [ int(int(key)/1000), response['data'][str(key)][1] ] )

	# sort data in ascending order
	values.sort()

	# clean up list of values. qloud stores each reading, although the value might be the same. Thus we clean here the data
	# Only the first occurrence of the energy value is needed
	energyValues = list()
	oldValue = 0
	for x in values:
		if x[1] > oldValue:
			oldValue = x[1]
			energyValues.append(x)
		else:
			values.remove(x)

	# calculate power values
	powerValues = list()

	for i in xrange(0, len(energyValues)-1):
		deltaT = energyValues[i+1][0] - energyValues[i][0]
		deltaE = energyValues[i+1][1] - energyValues[i][1]
		powerValues.append([energyValues[i][0], float(deltaE*3600000)/deltaT])
		# print energyValues[i][0], float(deltaE*3600000)/deltaT

	print powerValues

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
	starttime = config.get('Sensor1', 'start')

	getData(user, password, uuid1, starttime)

	# Start the scheduler
	# sched = BlockingScheduler()

	# sched.add_job(lambda: getData(apiConnection, header, uuid1), 'interval', seconds=int(60))
	# sched.start()
