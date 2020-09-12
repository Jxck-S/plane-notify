import requests
import configparser
import json
import time
from planeClass import Plane
main_config = configparser.ConfigParser()
main_config.read('mainconf.ini')
import os
#Set ADSBX URL Based off amount of Conf files
if main_config.get('DATA', 'SOURCE') == "ADSBX":
    planes = {}
    for filename in os.listdir(os. getcwd()):
        if filename.endswith(".ini") and filename != "mainconf.ini":
            plane_config = configparser.ConfigParser()
            plane_config.read(filename)
            planes[plane_config.get('DATA', 'ICAO').upper()] = Plane(plane_config.get('DATA', 'ICAO'), filename)
    if len(planes) > 1:
        url = "https://adsbexchange.com/api/aircraft/json/"
    elif len(planes) == 1:
        url = "https://adsbexchange.com/api/aircraft/icao/" +  str(list(planes.keys())[0]) + "/"

    headers = {
        'api-auth': main_config.get('ADSBX', 'API_KEY'),
        'Content-Encoding': 'gzip'
    }
elif main_config.get('DATA', 'SOURCE') == "OPENS":
    raise NotImplementedError
while True:
    if main_config.get('DATA', 'SOURCE') == "ADSBX":
        try:
            response = requests.get(url, headers = headers)
            data = response.text
            data = json.loads(data)
            failed = False
        except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as error_message:
            print("ADSBX Connection Error")
            print(error_message)
            failed = True
        except json.decoder.JSONDecodeError as error_message:
            print("Error with JSON")
            print(error_message)
            failed = True

        if failed == False:
            print(data)
            if data['ac'] != None:
                for planeData in data['ac']:
                    for key, obj in planes.items():
                        if planeData['icao'] == key:
                            print(planeData['icao'])
                            print(planeData)
                            obj.run(planeData)
                        else:
                            obj.run(None)
            else:
                for obj in planes.values():
                    obj.run(None)


    time.sleep(15)
