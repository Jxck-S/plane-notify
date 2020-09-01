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
        url = "https://adsbexchange.com/api/aircraft/icao/" +  next(iter(planes.values())).upper() + "/"

    headers = {
        'api-auth': main_config.get('ADSBX', 'API_KEY'),
        'Content-Encoding': 'gzip'
    }
if main_config.get('DATA', 'SOURCE') == "OPENS":
    raise NotImplementedError
while True:
    if main_config.get('DATA', 'SOURCE') == "ADSBX":
        response = requests.get(url, headers = headers)
        data = response.text
        data = json.loads(data)
        for planeData in data:
            for obj in planes:
                if planeData['icao'] == obj.getICAO:
                    obj.run(planeData)
                else:
                    obj.run(None)


    time.sleep(15)
