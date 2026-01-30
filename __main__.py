from cnf_parser_ext import ConfigParserExt
import time
from colorama import Fore, Back, Style
import platform
import traceback
import os, shutil
import logging
import tempfile
import sys
from plane import Plane
from datetime import datetime
import pytz
import signal
from colorama import init
from utils import clean_stack_trace
from threading import Thread
from heartbeat_server import Heartbeat
from config_manager import ConfigManager
from heartbeat_server import run_heartbeat_server
from socials.discord import sendDis
import ast
from readsb import pull_date_ras as pull_date_ras_readsb, pull_readsb
from defADSBX import pull_date_ras as pull_date_ras_adsbx
from defRpdADSBX import pull_rpdadsbx
from defOpenSky import pull_opensky
if platform.system() == "Windows":
    init(convert=True)

tmp_dir = tempfile.gettempdir()
notify_dir = os.path.join(tmp_dir, "plane-notify")

if os.path.exists(notify_dir):
    shutil.rmtree(notify_dir)

os.makedirs(notify_dir)
os.makedirs(os.path.join(notify_dir, "imgs"))

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

sys.path.extend([os.getcwd()])

#Dependency Handling
if not os.path.isdir("./dependencies/"):
    os.mkdir("./dependencies/")

required_files = [
("Roboto-Regular.ttf", 'https://github.com/googlefonts/roboto/blob/main/src/hinted/Roboto-Regular.ttf?raw=true')
]
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

main_config = ConfigParserExt()
print(os.getcwd())
main_config.read('./configs/mainconf.ini')
source = main_config.get('DATA', 'SOURCE')


heartbeat = Heartbeat()
server_thread = Thread(target=run_heartbeat_server, args=(heartbeat,), name="heartbeat")  # Pass function and arguments properly
server_thread.daemon = True
server_thread.start()

if main_config.getboolean('DISCORD', 'ENABLE'):
        role_id = main_config.get('DISCORD', 'ROLE_ID') if main_config.has_option('DISCORD', 'ROLE_ID') and main_config.get('DISCORD', 'ROLE_ID').strip() != "" else None
        sendDis("Started", main_config, role_id = role_id)
def service_exit(signum, frame):
    if main_config.getboolean('DISCORD', 'ENABLE'):
        role_id = main_config.get('DISCORD', 'ROLE_ID') if main_config.has_option('DISCORD', 'ROLE_ID') and main_config.get('DISCORD', 'ROLE_ID').strip() != "" else None
        sendDis("Service Stop", main_config, role_id = role_id)
    raise SystemExit("Service Stop")
signal.signal(signal.SIGTERM, service_exit)
if os.path.isfile("lookup_route.py"):
    print("Route lookup is enabled")
else:
    print("Route lookup is disabled")


#For Error output
plane = None
try:
    print("Source is set to", source)
    import sys
    #Setup plane objects from plane configs using ConfigManager
    planes = []  # Changed from {} dict to [] list
    config_manager = ConfigManager("./configs")
    config_manager.load_all_configs(planes)
    
    # Link config manager to heartbeat for /reload endpoint
    heartbeat.set_config_manager(config_manager, planes)

    running_Count = 0
    try:
        tz = pytz.timezone(main_config.get('DATA', 'TZ'))
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.UTC
    last_ra_count = None
    while True:
        # Check for reload request from /reload endpoint
        if heartbeat.check_and_clear_reload():
            stats = config_manager.reload_all_configs(planes)
            heartbeat.reload_stats = stats
        
        heartbeat.update_timestamp()
        datetime_tz = datetime.now(tz)
        if datetime_tz.hour == 0 and datetime_tz.minute == 0:
            running_Count = 0
        running_Count +=1
        start_time = time.time()
        header = ("-------- " + str(running_Count) + " -------- " + str(datetime_tz.strftime("%I:%M:%S %p")) + " ---------------------------------------------------------------------------")
        print (Back.GREEN +  Fore.BLACK + header[0:100] + Style.RESET_ALL)
        if source == "READSB":
            #ACAS/TCAS data
            today = datetime.utcnow()
            date = today.strftime("%Y/%m/%d")
            ras = pull_date_ras_readsb(date)
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
                        if ra['hex'].lower() in planes:
                            if ra['hex'].lower() not in sorted_ras:
                                sorted_ras[ra['hex'].lower()] = [ra]
                            else:
                                sorted_ras[ra['hex'].lower()].append(ra)
                else:
                    print("No new Resolution Advisories")
                last_ra_count = ra_count
            # Check for RAs for each plane
            for plane in planes:
                if sorted_ras != {} and plane.icao in sorted_ras:
                    print(plane.icao, "has", len(sorted_ras[plane.icao]), "RAs")
                    plane.check_new_ras(sorted_ras[plane.icao])
                elif sorted_ras != {} and plane.pia_icao and plane.pia_icao in sorted_ras:
                    print(plane.pia_icao, "has", len(sorted_ras[plane.pia_icao]), "RAs")
                    plane.check_new_ras(sorted_ras[plane.pia_icao])
                plane.expire_ra_types()
            #Normal API data
            icao_key = 'hex'
            data = pull_readsb(planes)
            if data is not None:
                main_key = 'aircraft' if 'aircraft' in data else 'ac'
                if data[main_key]:
                    data_indexed = {}
                    #Indexing the data by hex/icao code
                    for planeData in data[main_key]:
                        hex_lower = planeData[icao_key].lower()
                        data_indexed[hex_lower] = planeData
                    #Iterating through planes and matching with indexed data
                    for plane in planes:
                        # Check if we have data for this plane's primary ICAO or PIA_ICAO
                        hex_data = None
                        is_pia = False
                        
                        if plane.icao in data_indexed:
                            hex_data = data_indexed[plane.icao]
                            is_pia = False
                        elif plane.pia_icao and plane.pia_icao in data_indexed:
                            hex_data = data_indexed[plane.pia_icao]
                            is_pia = True
                        
                        if hex_data:
                            plane.run_readsb(hex_data, is_pia)
                        else:
                            plane.run_empty()
                else:
                    for plane in planes.values():
                        plane.run_empty()
        elif source == "RpdADSBX":
            #ACAS data
            today = datetime.utcnow()
            date = today.strftime("%Y/%m/%d")
            ras = pull_date_ras_adsbx(date)
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
                        if ra['hex'].lower() in planes:
                            if ra['hex'].lower() not in sorted_ras:
                                sorted_ras[ra['hex'].lower()] = [ra]
                            else:
                                sorted_ras[ra['hex'].lower()].append(ra)
                else:
                    print("No new Resolution Advisories")
                last_ra_count = ra_count
            # Check for RAs for each plane
            for plane in planes:
                if sorted_ras != {} and plane.icao in sorted_ras:
                    print(plane.icao, "has", len(sorted_ras[plane.icao]), "RAs")
                    plane.check_new_ras(sorted_ras[plane.icao])
                elif sorted_ras != {} and plane.pia_icao and plane.pia_icao in sorted_ras:
                    print(plane.pia_icao, "has", len(sorted_ras[plane.pia_icao]), "RAs")
                    plane.check_new_ras(sorted_ras[plane.pia_icao])
                plane.expire_ra_types()
            #from defRpdADSBX import pull_rpdadsbx
            # Process each plane once
            for plane in planes:
                plane_info = pull_rpdadsbx(plane.icao)
                if plane_info:
                    if plane_info['ac']:
                        plane.run_readsb(plane_info['ac'][0], is_pia=False)
                    else:
                        plane.run_empty()
                else:
                    print(f"No data for icao {plane.icao}. Skipping...")
                    plane.run_empty()
        elif source == "OPENS":
            planeData, failed = pull_opensky(planes)
            if failed == False:
                if planeData != None and planeData.states != []:
                    # Process each plane
                    for plane in planes:
                        has_data = False
                        for dataState in planeData.states:
                            if (dataState.icao24).lower() == plane.icao:
                                plane.run_opens(dataState, is_pia=False)
                                has_data = True
                                break
                            elif plane.pia_icao and (dataState.icao24).lower() == plane.pia_icao:
                                plane.run_opens(dataState, is_pia=True)
                                has_data = True
                                break
                        if has_data is False:
                            plane.run_empty()
                else:
                    # No data, run empty for all planes
                    for plane in planes:
                        plane.run_empty()
        elapsed_calc_time = time.time() - start_time
        datetime_tz = datetime.now(tz)
        footer = "-------- " + str(running_Count) + " -------- " + str(datetime_tz.strftime("%I:%M:%S %p")) + " ------------------------Elapsed Time- " + str(round(elapsed_calc_time, 3)) + " -------------------------------------"
        print (Back.GREEN + Fore.BLACK + footer[0:100] + Style.RESET_ALL)

        if main_config.has_section('SLEEP'):
            sleep_sec = int(main_config.get('SLEEP', 'SLEEPSEC'))
        else:
            sleep_sec = 10
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
        sendDis(str("Manual Exit: " + str(e)), main_config)
except Exception as e:
    if main_config.getboolean('DISCORD', 'ENABLE'):
        try:
            os.remove('crash_latest.log')
        except OSError:
            pass
        clean_e = clean_stack_trace(str(e))
        logging.basicConfig(filename='crash_latest.log', filemode='w', format='%(asctime)s - %(message)s')
        logging.Formatter.converter = time.gmtime
        logging.error(e)
        logging.error(clean_stack_trace(str(traceback.format_exc())))
        error_message = f"Error Exiting: {type(e)} " + clean_e 
        if plane:
            error_message += f"\nFailed on ({plane.config_path}) - {plane.icao}"
        sendDis(error_message, main_config, role_id, "crash_latest.log")
    raise e
