import requests
import configparser
import json
import time
from colorama import Fore, Back, Style
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
running_Count = 0
while True:
    running_Count +=1
    start_time = time.time()
    print (Back.GREEN,  Fore.BLACK, "--------", running_Count, "-------------------------------------------------------", Style.RESET_ALL)
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
            print (json.dumps(data, indent = 2))
            print(error_message)
            failed = True

        if failed == False:
            if data['ac'] != None:
                for key, obj in planes.items():
                    has_data = False
                    for planeData in data['ac']:
                        if planeData['icao'] == key:
                            obj.run(planeData)
                            has_data = True
                            break
                    if has_data is False:
                        obj.run(None)
            else:
                for obj in planes.values():
                    obj.run(None)
    elapsed_calc_time = time.time() - start_time
    print (Back.GREEN,  Fore.BLACK, "--------", running_Count, "------------------------Elapsed Time-", elapsed_calc_time, " -------------------------------------", Style.RESET_ALL)
    print(Back.RED, "Sleep 30", Style.RESET_ALL)
    time.sleep(30)

