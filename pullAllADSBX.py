import requests
import configparser
import json
main_config = configparser.ConfigParser()
main_config.read('mainconf.ini')
import os
#Set ADSBX URL Based off amount of Conf files
if main_config.get('DATA', 'SOURCE') == "ADSBX":
    for filename in os.listdir(os. getcwd()):
        if filename.endswith(".ini") and filename != "mainconf.ini":
            plane_config = configparser.ConfigParser()
            plane_config.read(filename)
            plane_config.get('DATA', 'ICAO')
            icao_list = []
            icao_list.append(plane_config.get('DATA', 'ICAO'))
    if len(icao_list) > 1:
        url = "https://adsbexchange.com/api/aircraft/json/"
    elif len(icao_list) == 1:
        url = "https://adsbexchange.com/api/aircraft/icao/" + icao_list[0].upper() + "/"

    headers = {
        'api-auth': main_config.get('ADSBX', 'API_KEY'),
        'Content-Encoding': 'gzip'
    }
if main_config.get('DATA', 'SOURCE') == "OPENS":

while True:
    if main_config.get('DATA', 'SOURCE') == "ADSBX":
        response = requests.get(url, headers = headers)
        data = response.text
        data = json.loads(data)
        for plane in data['ac']:
            if plane['icao'] == "4074B8":
        print(plane)
#print(json.dumps(data, indent=2))
print("done")
#Initate Each Plane Object from their configs



        plane_config = configparser.ConfigParser()
        plane_config.read(filename)
        print(filename)
        print(plane_config.get('ADSBX', 'API_KEY'))
