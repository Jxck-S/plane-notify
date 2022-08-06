import configparser
from logging import DEBUG
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
import signal
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
import sys
sys.path.extend([os.getcwd()])
#Dependency Handling
if not os.path.isdir("./dependencies/"):
    os.mkdir("./dependencies/")
required_files = [("Roboto-Regular.ttf", 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Regular.ttf?raw=true'), ('airports.csv', 'https://ourairports.com/data/airports.csv'), ('regions.csv', 'https://ourairports.com/data/regions.csv'), ('ADSBX_Logo.png', "https://www.adsbexchange.com/wp-content/uploads/cropped-Stealth.png"), ('Mictronics_db.zip', "https://www.mictronics.de/aircraft-database/indexedDB.php")]
for file in required_files:
	file_name = file[0]
	url = file[1]
	if not os.path.isfile("./dependencies/" + file_name):
		print(file_name,  "does not exist downloading now")
		try:
			import requests
			file_content = requests.get(url)

			open(("./dependencies/" + file_name), 'wb').write(file_content.content)
		except Exception as e:
			raise e("Error getting", file_name, "from", url)
		else:
			print("Successfully got", file_name)
	else:
		print("Already have", file_name, "continuing")
if os.path.isfile("./dependencies/" + required_files[4][0]) and not os.path.isfile("./dependencies/aircrafts.json"):
    print("Extracting Mictronics DB")
    from zipfile import ZipFile
    with ZipFile("./dependencies/" + required_files[4][0], 'r') as mictronics_db:
        mictronics_db.extractall("./dependencies/")

main_config = configparser.ConfigParser()
print(os.getcwd())
main_config.read('./configs/mainconf.ini')
source = main_config.get('DATA', 'SOURCE')
if main_config.getboolean('DISCORD', 'ENABLE'):
        from defDiscord import sendDis
        sendDis("Started", main_config, role_id = main_config.get('DISCORD', 'ROLE_ID'))
def service_exit(signum, frame):
    if main_config.getboolean('DISCORD', 'ENABLE'):
        from defDiscord import sendDis
        sendDis("Service Stop", main_config, role_id = main_config.get('DISCORD', 'ROLE_ID'))
    raise SystemExit("Service Stop")
signal.signal(signal.SIGTERM, service_exit)
if os.path.isfile("lookup_route.py"):
    print("Route lookup is enabled")
else:
    print("Route lookup is disabled")

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
    last_ra_count = None
    print(len(planes), "Planes configured")
    while True:
        datetime_tz = datetime.now(tz)
        if datetime_tz.hour == 0 and datetime_tz.minute == 0:
            running_Count = 0
        running_Count +=1
        start_time = time.time()
        header = ("-------- " + str(running_Count) + " -------- " + str(datetime_tz.strftime("%I:%M:%S %p")) + " ---------------------------------------------------------------------------")
        print (Back.GREEN +  Fore.BLACK + header[0:100] + Style.RESET_ALL)
        if source == "ADSBX":
            #ACAS data
            from defADSBX import pull_date_ras
            import ast
            today = datetime.utcnow()
            date = today.strftime("%Y/%m/%d")
            ras = pull_date_ras(date)
            sorted_ras = {}
            if ras is not None:
                #Testing RAs
                #if last_ra_count is not None:
                #    with open('./testing/acastest.json') as f:
                #        data = f.readlines()
                #    ras += data
                ra_count = len(ras)
                if last_ra_count is not None and ra_count != last_ra_count:
                    print(abs(ra_count - last_ra_count), "new Resolution Advisories")
                    for ra_num, ra in enumerate(ras[last_ra_count:]):
                        ra = ast.literal_eval(ra)
                        if ra['hex'].upper() in planes.keys():
                            if ra['hex'].upper() not in sorted_ras.keys():
                                sorted_ras[ra['hex'].upper()] = [ra]
                            else:
                                sorted_ras[ra['hex'].upper()].append(ra)
                else:
                    print("No new Resolution Advisories")
                last_ra_count = ra_count
            for key, obj in planes.items():
                if sorted_ras != {} and key in sorted_ras.keys():
                        print(key, "has", len(sorted_ras[key]), "RAs")
                        obj.check_new_ras(sorted_ras[key])
                obj.expire_ra_types()
            #Normal API data
            api_version = int(main_config.get('ADSBX', 'API_VERSION'))
            if api_version == 2:
                icao_key = 'hex'
            elif api_version == 1:
                icao_key = 'icao'
            else:
                raise ValueError("Invalid API Version")
            from defADSBX import pull_adsbx
            data = pull_adsbx(planes)
            if data is not None:
                if data['ac'] is not None:
                    data_indexed = {}
                    for planeData in data['ac']:
                        data_indexed[planeData[icao_key].upper()] = planeData
                    for key, obj in planes.items():
                        if key in data_indexed.keys():
                            if api_version == 1:
                                obj.run_adsbx_v1(data_indexed[key.upper()])
                            elif api_version == 2:
                                obj.run_adsbx_v2(data_indexed[key.upper()])
                        else:
                            obj.run_empty()
                else:
                    for obj in planes.values():
                        obj.run_empty()
            else:
                failed_count += 1
        elif source == "OPENS":
            from defOpenSky import pull_opensky
            planeData, failed = pull_opensky(planes)
            if failed == False:
                if planeData != None and planeData.states != []:
                    #   print(planeData.time)
                    for key, obj in planes.items():
                        has_data = False
                        for dataState in planeData.states:
                            if (dataState.icao24).upper() == key:
                                obj.run_opens(dataState)
                                has_data = True
                                break
                        if has_data is False:
                            obj.run_empty()
                else:
                    for obj in planes.values():
                        obj.run_empty()
            elif failed:
                failed_count += 1
        elif source == "FACHADEV":
            from defApiFachaDev import pull_apiFachaDev
            planeData, failed = pull_apiFachaDev(planes)
            if failed == False:
                if planeData != None and planeData != []:
                    for key, obj in planes.items():
                        has_data = False
                        for dataState in planeData:
                            if (dataState['icao']).upper() == key:
                                # print(dataState)
                                obj.run_fachadev(dataState)
                                has_data = True
                                break
                        if has_data is False:
                            obj.run_empty()
                else:
                    for obj in planes.values():
                        obj.run_empty()
            elif failed:
                failed_count += 1
        if failed_count >= 10 and main_config.getboolean('DATA', 'FAILOVER'):
            if source == "OPENS":
                source = "ADSBX"
            elif source == "ADSBX":
                source = "OPENS"
            failed_count = 0
            if main_config.getboolean('DISCORD', 'ENABLE'):
                from defDiscord import sendDis
                sendDis(str("Failed over to " + source), main_config)
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
        from defDiscord import sendDis
        sendDis(str("Manual Exit: " + str(e)), main_config)
except Exception as e:
    if main_config.getboolean('DISCORD', 'ENABLE'):
        try:
            os.remove('crash_latest.log')
        except OSError:
            pass
        import logging
        logging.basicConfig(filename='crash_latest.log', filemode='w', format='%(asctime)s - %(message)s',level=logging.DEBUG)
        logging.Formatter.converter = time.gmtime
        logging.error(e)
        logging.error(str(traceback.format_exc()))
        from defDiscord import sendDis
        sendDis(str("Error Exiting: " + str(e) + " Failed on " + "https://globe.adsbexchange.com/?icao=" + key), main_config, main_config.get('DISCORD', 'ROLE_ID'), "crash_latest.log")
    raise e