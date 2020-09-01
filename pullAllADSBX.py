import requests
import configparser
import json
main_config = configparser.ConfigParser()
main_config.read('config.ini')
url = "https://adsbexchange.com/api/aircraft/json/"
headers = {
    'api-auth': main_config.get('ADSBX', 'API_KEY'),
    'Content-Encoding': 'gzip'
}

response = requests.get(url, headers = headers)
data = response.text
data = json.loads(data)

#Test Parse
for plane in data['ac']:
    if plane['icao'] == "4074B8":
        print(plane)
#print(json.dumps(data, indent=2))
print("done")
#Initate Each Plane Object from their configs
import os
for filename in os.listdir(os. getcwd()):
    if filename.endswith(".ini") and filename != "mainconf.ini":
        plane_config = configparser.ConfigParser()
        plane_config.read(filename)
        print(filename)
        print(plane_config.get('ADSBX', 'API_KEY'))
