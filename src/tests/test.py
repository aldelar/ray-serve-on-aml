import requests
import urllib.request

import json

# 3: Query the deployment and print the result.
# print(requests.get("http://localhost:8000/hello", params={"name": "Theodore"}).json())
# "Hello Theodore!"

print(requests.get("http://localhost:8000/get_bind_nodes").json())
print()

# data ={"new_name":"NEW_WORKSHOP_NAME"}
data ="NEW WORKSHOP"
# print(requests.post("http://localhost:8000/set_workshop_name", json=data).json())


def set_workshop_name(data):

    # body = str.encode(json.dumps({"mapping":mapping}))
    body = str.encode(json.dumps({"new_name":data}))
    # body = str.encode(data)
    base_uri = "http://localhost:8000"

    url = f'{base_uri}/set_workshop_name'

    headers = {'Content-Type':'application/json'}

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        print(json.loads(result))
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))

set_workshop_name(data)