# based on https://q-loud.de/api/example.html

import httplib
import json

# get session information on api.cospace.de
initialConnection = httplib.HTTPSConnection("api.cospace.de")
initialConnection.request("GET", "/api/session")

# result is JSON encoded
response = json.loads(initialConnection.getresponse().read())

print response
print "get session response: " + str(response)

# cut https:// prefix (7 characters) from server returned in JSON
apiServer = response["server"][8:]

# remember the session id
sid = response["sid"]

# create the connection for the following API requests
apiConnection = httplib.HTTPSConnection(apiServer)

# post credentials into session
body = json.dumps({
    "username": "",
    "password": ""
})

headers = {"Authorization": "Bearer " + sid}
apiConnection.request("POST", "/api/session", body, headers=headers)
response = json.loads(apiConnection.getresponse().read())
print "login response: " + str(response)


apiConnection.request("GET", "/api/user", headers=headers)
response = json.loads(apiConnection.getresponse().read())
print "get user details: " + str(response)

# remember the John's "tag_all" to access his objects later
tagAll = response["user"]["tag_all"]
apiConnection.request("GET", "/api/tag/" + tagAll + "/object", headers=headers)
response = json.loads(apiConnection.getresponse().read())
print "user's objects: " + str(response)
