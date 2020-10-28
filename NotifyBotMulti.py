import requests
import configparser
import json
import time
from defADSBX import pullADSBX
from defOpenSky import pullOpenSky
from colorama import Fore, Back, Style
import platform
if platform.system() == "Windows":
    from colorama import init
    init(convert=True)
from planeClass import Plane
from datetime import datetime
import pytz
main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')
import os
import sys
#Setup Plane Objects off of Plane configs
planes = {}
for filename in os.listdir("./configs"):
    if filename.endswith(".ini") and filename != "mainconf.ini":
        plane_config = configparser.ConfigParser()
        plane_config.read(("./configs/" + filename))
        planes[plane_config.get('DATA', 'ICAO').upper()] = Plane(plane_config.get('DATA', 'ICAO'), filename)

running_Count = 0
try:
    tz = pytz.timezone(main_config.get('DATA', 'TZ'))
except pytz.exceptions.UnknownTimeZoneError:
    tz = pytz.UTC

while True:
    datetime_tz = datetime.now(tz)
    if datetime_tz.hour == 0 and datetime_tz.minute == 0:
        running_Count = 0
    running_Count +=1
    start_time = time.time()
    print (Back.GREEN,  Fore.BLACK, "--------", running_Count, "--------", datetime_tz.strftime("%I:%M:%S %p"), "-------------------------------------------------------", Style.RESET_ALL)
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
    elif main_config.get('DATA', 'SOURCE') == "OPENS":
        planeData, failed = pullOpenSky(planes)
        if failed == False:
            if planeData.states != []:
                #   print(planeData.time)
                for key, obj in planes.items():
                    has_data = False
                    for dataState in planeData.states:
                        if (dataState.icao24).upper() == key:
                            obj.run(dataState)
                            has_data = True
                            break
                    if has_data is False:
                        obj.run(None)
            else:
                for obj in planes.values():
                    obj.run(None)
    elapsed_calc_time = time.time() - start_time
    datetime_tz = datetime.now(tz)
    print (Back.GREEN,  Fore.BLACK, "--------", running_Count, "--------", datetime_tz.strftime("%I:%M:%S %p"), "------------------------Elapsed Time-", elapsed_calc_time, " -------------------------------------", Style.RESET_ALL)


    sleep_sec = 20
    for i in range(sleep_sec,0,-1):
        if i < 10:
            i = " " + str(i)
        sys.stdout.write("\r")
        sys.stdout.write(Back.RED + "Sleep {00000000}".format(i) + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(1)
    sys.stdout.write(Back.RED + ('\x1b[1K\r' +"Slept for " +str(sleep_sec)) + Style.RESET_ALL)
    print()

