import configparser
import time
from colorama import Fore, Back, Style
import platform
import traceback
if platform.system() == "Windows":
    from colorama import init
    init(convert=True)
from planeClass import Plane
from datetime import datetime
import pytz
import os
if 'plane-notify' not in os.getcwd():
    os.chdir('./plane-notify')
import sys
sys.path.extend([os.getcwd()])
required_files = [("Roboto-Regular.ttf", 'https://github.com/google/fonts/raw/master/apache/roboto/static/Roboto-Regular.ttf'), ('airports.csv', 'https://ourairports.com/data/airports.csv'), ('regions.csv', 'https://ourairports.com/data/regions.csv')]
for file in required_files:
	file_name = file[0]
	url = file[1]
	if not os.path.isfile(file_name):
		print(file_name,  "does not exist downloading now")
		try:
			import requests
			file_content = requests.get(url)

			open(file_name, 'wb').write(file_content.content)
		except:
			raise("Error getting", file_name, "from", url)
		else:
			print("Successfully got", file_name)
	elif os.path.isfile(file_name):
		print("Already have", file_name, "continuing")
main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')
source = main_config.get('DATA', 'SOURCE')
if main_config.getboolean('DISCORD', 'ENABLE'):
    from discord_webhook import DiscordWebhook
    webhook = DiscordWebhook(url= main_config.get('DISCORD', 'URL'), content=(str("Started")))
    webhook.execute()
try:
    print("Source is set to", source)
    import sys
    #Setup plane objects from plane configs
    planes = {}
    print("Found the following configs")
    for dirpath, dirname, filename in os.walk("./configs"):
            for filename in [f for f in filename if f.endswith(".ini") and f != "mainconf.ini"]:
                if not "disabled" in dirpath:
                    print(os.path.join(dirpath, filename))
                    plane_config = configparser.ConfigParser()
                    plane_config.read((os.path.join(dirpath, filename)))
                    #Creates a Key labeled the ICAO of the plane, with the value being a plane object
                    planes[plane_config.get('DATA', 'ICAO').upper()] = Plane(plane_config.get('DATA', 'ICAO'), os.path.join(dirpath, filename), plane_config)

    running_Count = 0
    failed_count = 0
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
        header = ("-------- " + str(running_Count) + " -------- " + str(datetime_tz.strftime("%I:%M:%S %p")) + " ---------------------------------------------------------------------------")
        print (Back.GREEN +  Fore.BLACK + header[0:100] + Style.RESET_ALL)
        if source == "ADSBX":
            api_version = int(main_config.get('ADSBX', 'API_VERSION'))
            if api_version == 2:
                icao_key = 'hex'
            elif api_version == 1:
                icao_key = 'icao'
            else:
                raise Exception("Invalid API Version")
            from defADSBX import pullADSBX
            data, failed = pullADSBX(planes)
            if failed == False:
                if data['ac'] != None:
                    for key, obj in planes.items():
                        has_data = False
                        for planeData in data['ac']:
                            if planeData[icao_key].upper() == key:
                                if api_version == 1:
                                    obj.run_ADSBXv1(planeData)
                                elif api_version == 2:
                                    obj.run_ADSBXv2(planeData)
                                has_data = True
                                break
                        if has_data is False:
                            obj.run_empty()
                else:
                    for obj in planes.values():
                        obj.run_empty()
            elif failed:
                failed_count += 1
        elif source == "OPENS":
            from defOpenSky import pullOpenSky
            planeData, failed = pullOpenSky(planes)
            if failed == False:
                if planeData.states != []:
                    #   print(planeData.time)
                    for key, obj in planes.items():
                        has_data = False
                        for dataState in planeData.states:
                            if (dataState.icao24).upper() == key:
                                obj.run_OPENS(dataState)
                                has_data = True
                                break
                        if has_data is False:
                            obj.run_empty()
                else:
                    for obj in planes.values():
                        obj.run_empty()
            elif failed:
                failed_count += 1
        if failed_count >= 10:
            if source == "OPENS":
                source = "ADSBX"
            elif source == "ADSBX":
                source = "OPENS"
            failed_count = 0
            if main_config.getboolean('DISCORD', 'ENABLE'):
                webhook = DiscordWebhook(url= main_config.get('DISCORD', 'URL'), content=(str("Failed over to " + source)))
                webhook.execute()
        elapsed_calc_time = time.time() - start_time
        datetime_tz = datetime.now(tz)
        footer = "-------- " + str(running_Count) + " -------- " + str(datetime_tz.strftime("%I:%M:%S %p")) + " ------------------------Elapsed Time- " + str(round(elapsed_calc_time, 3)) + " -------------------------------------"
        print (Back.GREEN + Fore.BLACK + footer[0:100] + Style.RESET_ALL)


        sleep_sec = 30
        for i in range(sleep_sec,0,-1):
            if i < 10:
                i = " " + str(i)
            sys.stdout.write("\r")
            sys.stdout.write(Back.RED + "Sleep {00000000}".format(i) + Style.RESET_ALL)
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write(Back.RED + ('\x1b[1K\r' +"Slept for " +str(sleep_sec)) + Style.RESET_ALL)
        print()
except KeyboardInterrupt as e:
    print(e)
    if main_config.getboolean('DISCORD', 'ENABLE'):
        webhook = DiscordWebhook(url= main_config.get('DISCORD', 'URL'), content=(str("Manual Exit: " + str(e) )))
        webhook.execute()
except BaseException as e:
    print(e)
    print(traceback.format_exc())
    if main_config.getboolean('DISCORD', 'ENABLE'):
        webhook = DiscordWebhook(url= main_config.get('DISCORD', 'URL'), content=(str("Error Exiting: " + str(e) )))
        webhook.execute()