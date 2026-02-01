import ast
import os
import platform
import shutil
import signal
import sys
import tempfile
import time
import traceback
from datetime import UTC, datetime

from colorama import Back, Fore, Style, init

import socials.discord as discord
from cnf_parser_ext import ConfigParserExt
from config_manager import ConfigManager
from readsb import pull_date_ras as pull_date_ras_readsb
from readsb import pull_readsb
from utils import clean_stack_trace
from web.server import start_web_server

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
project_root = os.path.dirname(dname)
os.chdir(project_root)

sys.path.extend([project_root, dname])

# Dependency Handling
if not os.path.isdir("./dependencies/"):
    os.mkdir("./dependencies/")


main_config = ConfigParserExt()
print(os.getcwd())
main_config.read("./configs/mainconf.ini")

import db

db.init_db(main_config)


if main_config.getboolean("DISCORD", "ENABLE"):
    role_id = (
        main_config.get("DISCORD", "ROLE_ID")
        if main_config.has_option("DISCORD", "ROLE_ID")
        and main_config.get("DISCORD", "ROLE_ID").strip() != ""
        else None
    )
    discord.post("Started", main_config, role_id=role_id)


def service_exit(signum, frame):
    if main_config.getboolean("DISCORD", "ENABLE"):
        role_id = (
            main_config.get("DISCORD", "ROLE_ID")
            if main_config.has_option("DISCORD", "ROLE_ID")
            and main_config.get("DISCORD", "ROLE_ID").strip() != ""
            else None
        )
        discord.post("Service Stop", main_config, role_id=role_id)
    raise SystemExit("Service Stop")


signal.signal(signal.SIGTERM, service_exit)
if os.path.isfile("lookup_route.py"):
    print("Route lookup is enabled")
else:
    print("Route lookup is disabled")


# For Error output
plane = None
try:
    import sys

    # Setup plane objects from plane configs using ConfigManager
    planes = []  # Changed from {} dict to [] list
    from notification_manager import NotificationManager

    # Initialize global sources (Reddit)
    NotificationManager.init_sources(main_config)

    config_manager = ConfigManager("./configs")
    config_manager.load_all_configs(planes)

    # Link config manager to heartbeat for /reload endpoint
    start_web_server(config_manager, planes)

    while True:
        # Check for reload request from /reload endpoint

        datetime_now = datetime.now()
        start_time = time.time()
        header = (
            "---------------- "
            + str(datetime_now.strftime("%I:%M:%S %p"))
            + " ---------------------------------------------------------------------------"
        )
        print(Back.GREEN + Fore.BLACK + header[0:100] + Style.RESET_ALL)
        # ACAS/TCAS data
        today = datetime.now(UTC)
        date = today.strftime("%Y/%m/%d")
        ras = pull_date_ras_readsb(date)
        sorted_ras = {}
        if ras is not None:
            # Testing RAs
            # if last_ra_count is not None:
            #    with open('./testing/acastest.json') as f:
            #        data = f.readlines()
            #    ras += data
            ra_count = len(ras)
            if last_ra_count is not None and ra_count != last_ra_count:
                print(abs(ra_count - last_ra_count), "new Resolution Advisories")
                for ra_num, ra in enumerate(ras[last_ra_count:]):
                    ra = ast.literal_eval(ra)
                    if ra["hex"].lower() in planes:
                        if ra["hex"].lower() not in sorted_ras:
                            sorted_ras[ra["hex"].lower()] = [ra]
                        else:
                            sorted_ras[ra["hex"].lower()].append(ra)
            else:
                print("No new Resolution Advisories")
            last_ra_count = ra_count
        # Check for RAs for each plane
        # Check for RAs for each plane
        # Use config_manager lock to safely iterate planes during potential reload
        # Lock covers the entire processing block to prevent interleaved logs with reload
        with config_manager.lock:
            for plane in planes:
                if sorted_ras != {} and plane.icao in sorted_ras:
                    print(plane.icao, "has", len(sorted_ras[plane.icao]), "RAs")
                    plane.check_new_ras(sorted_ras[plane.icao])
                elif (
                    sorted_ras != {} and plane.pia_icao and plane.pia_icao in sorted_ras
                ):
                    print(plane.pia_icao, "has", len(sorted_ras[plane.pia_icao]), "RAs")
                    plane.check_new_ras(sorted_ras[plane.pia_icao])
                plane.expire_ra_types()

            # Normal API data
            icao_key = "hex"

            # Pass safe copy if needed, but we hold lock now so safe to access planes
            data = pull_readsb(planes)
            if data is not None:
                main_key = "aircraft" if "aircraft" in data else "ac"
                if data[main_key]:
                    data_indexed = {}
                    # Indexing the data by hex/icao code
                    for planeData in data[main_key]:
                        hex_lower = planeData[icao_key].lower()
                        data_indexed[hex_lower] = planeData
                    # Iterating through planes and matching with indexed data
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
                    for plane in (
                        planes
                    ):  # Changed from planes.values() to planes as it's a list
                        plane.run_empty()

        elapsed_calc_time = time.time() - start_time
        footer = (
            "---------------- "
            + str(datetime_now.strftime("%I:%M:%S %p"))
            + " ------------------------Elapsed Time- "
            + str(round(elapsed_calc_time, 3))
            + " -------------------------------------"
        )
        print(Back.GREEN + Fore.BLACK + footer[0:100] + Style.RESET_ALL)

        if main_config.has_section("SLEEP"):
            sleep_sec = int(main_config.get("SLEEP", "SLEEPSEC"))
        else:
            sleep_sec = 10
        for i in range(sleep_sec, 0, -1):
            if i < 10:
                i = " " + str(i)
            sys.stdout.write("\r")
            sys.stdout.write(Back.RED + f"Sleep {i}" + Style.RESET_ALL)
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write(
            Back.RED + ("\x1b[1K\r" + "Slept for " + str(sleep_sec)) + Style.RESET_ALL
        )
        print()
except KeyboardInterrupt as e:
    print(e)
    if main_config.getboolean("DISCORD", "ENABLE"):
        discord.post(str("Manual Exit: " + str(e)), main_config)
except Exception as e:
    if main_config.getboolean("DISCORD", "ENABLE"):
        try:
            os.remove("crash_latest.log")
        except OSError:
            pass
        clean_e = clean_stack_trace(str(e))
        clean_e = clean_stack_trace(str(e))
        trace_output = clean_stack_trace(str(traceback.format_exc()))

        # Write directly to file to ensure it exists (basicConfig is ignored if already configured)
        with open("crash_latest.log", "w") as f:
            f.write(f"{datetime.now(UTC)} - {e}\n")
            f.write(f"{trace_output}\n")
        error_message = f"Error Exiting: {type(e)} " + clean_e
        if plane:
            error_message += f"\nFailed on ({plane.config_path}) - {plane.icao}"
        discord.post(error_message, main_config, role_id, "crash_latest.log")
    raise e
