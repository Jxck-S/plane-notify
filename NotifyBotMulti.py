import requests
import configparser
import json
import time
from defADSBX import pullADSBX
from colorama import Fore, Back, Style
from planeClass import Plane
main_config = configparser.ConfigParser()
main_config.read('mainconf.ini')
import os
#Setup Plane Objects off of Plane configs
if main_config.get('DATA', 'SOURCE') == "ADSBX":
    planes = {}
    for filename in os.listdir(os. getcwd()):
        if filename.endswith(".ini") and filename != "mainconf.ini":
            plane_config = configparser.ConfigParser()
            plane_config.read(filename)
            planes[plane_config.get('DATA', 'ICAO').upper()] = Plane(plane_config.get('DATA', 'ICAO'), filename)

elif main_config.get('DATA', 'SOURCE') == "OPENS":
    raise NotImplementedError
running_Count = 0
while True:
    running_Count +=1
    start_time = time.time()
    print (Back.GREEN,  Fore.BLACK, "--------", running_Count, "-------------------------------------------------------", Style.RESET_ALL)
    if main_config.get('DATA', 'SOURCE') == "ADSBX":
        data, failed = pullADSBX(planes)
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

