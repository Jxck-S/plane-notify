"""__main__.py: Entry point for the Plane Notify application."""

from __future__ import annotations


import argparse
import ast
import logging
import os
import platform
import shutil
import signal
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from typing import Never

from colorama import Back, Style, init

import db
from cnf_parser_ext import ConfigParserExt
from config_manager import ConfigManager
from logger import setup_logging
from readsb import pull_date_ras as pull_date_ras_readsb
from readsb import pull_readsb
from utils import clean_stack_trace
from web.server import start_web_server

if platform.system() == "Windows":
    init(convert=True)

tmp_dir = tempfile.gettempdir()
notify_dir = Path(tmp_dir) / "plane-notify"

if notify_dir.exists():
    shutil.rmtree(notify_dir)

notify_dir.mkdir(parents=True, exist_ok=True)
(notify_dir / "imgs").mkdir(parents=True, exist_ok=True)

abspath = Path(__file__).resolve()
dname = abspath.parent
project_root = dname.parent
os.chdir(project_root)

sys.path.extend([str(project_root), str(dname)])

# Dependency Handling
if not Path("./dependencies/").is_dir():
    Path("./dependencies/").mkdir()


# Arguments
parser = argparse.ArgumentParser(description="Plane Notify")
parser.add_argument("--debug", action="store_true", help="Enable debug logging")
args = parser.parse_args()

main_config = ConfigParserExt()
main_config.read("./configs/mainconf.ini")
# Setup Logging
setup_logging(main_config, debug=args.debug)
logger = logging.getLogger(__name__)
logger.info(Path.cwd())

db.init_db(main_config)


logger.warning("Started")


def service_exit(signum: int, frame: FrameType | None) -> Never:
    """Exit the service gracefully on receipt of a termination signal."""
    logger.warning("Service Stop")
    msg = "Service Stop"
    raise SystemExit(msg)


signal.signal(signal.SIGTERM, service_exit)
if Path("lookup_route.py").is_file():
    logger.info("Route lookup is enabled")
else:
    logger.info("Route lookup is disabled")


# For Error output
plane = None
try:
    # Setup plane objects from plane configs using ConfigManager
    planes = []  # Changed from {} dict to [] list
    from notification_manager import NotificationManager

    # Initialize global sources (Reddit)
    NotificationManager.init_sources(main_config)

    config_manager = ConfigManager("./configs")
    config_manager.load_all_configs(planes)

    # Link config manager to heartbeat for /reload endpoint
    web_host = main_config.get("WEB", "HOST", fallback="127.0.0.1")
    web_port = int(main_config.get("WEB", "PORT", fallback=8778))
    start_web_server(config_manager, planes, host=web_host, port=web_port)

    last_ra_count = None
    while True:
        # Check for reload request from /reload endpoint

        datetime_now = datetime.now()
        start_time = time.time()
        logger.debug("Begin Main Loop")

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
                logger.info(
                    "%s new Resolution Advisories", abs(ra_count - last_ra_count)
                )
                for ra in ras[last_ra_count:]:
                    ra = ast.literal_eval(ra)
                    if ra["hex"].lower() in planes:
                        if ra["hex"].lower() not in sorted_ras:
                            sorted_ras[ra["hex"].lower()] = [ra]
                        else:
                            sorted_ras[ra["hex"].lower()].append(ra)
            else:
                logger.info("No new Resolution Advisories")
            last_ra_count = ra_count
        # Check for RAs for each plane
        # Use config_manager lock to safely iterate planes during potential reload
        # Lock covers the entire processing block to prevent interleaved logs with reload
        with config_manager.lock:
            for plane in planes:
                if sorted_ras != {} and plane.icao in sorted_ras:
                    logger.info(
                        "%s has %s RAs", plane.icao, len(sorted_ras[plane.icao])
                    )
                    plane.check_new_ras(sorted_ras[plane.icao])
                elif (
                    sorted_ras != {} and plane.pia_icao and plane.pia_icao in sorted_ras
                ):
                    logger.info(
                        "%s has %s RAs", plane.pia_icao, len(sorted_ras[plane.pia_icao])
                    )
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
                    for plane_data in data[main_key]:
                        hex_lower = plane_data[icao_key].lower()
                        data_indexed[hex_lower] = plane_data
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
        logger.debug("End Main Loop - Elapsed Time: %s", round(elapsed_calc_time, 3))

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
        sys.stdout.write("\n")
except KeyboardInterrupt:
    logger.warning("Manual Exit")

except Exception as e:
    clean_e = clean_stack_trace(str(e))

    error_message = f"Error Exiting: {type(e)} " + clean_e
    if plane:
        error_message += f"\nFailed on ({plane.config_path}) - {plane.icao}"

    logger.exception(error_message)
    raise
