import json
import logging
import os
import tempfile
import time
from datetime import UTC, datetime, timedelta

import requests
import staticmaps
from colorama import Fore, Style
from geopy.distance import geodesic
from PIL import Image
from requests.exceptions import (
    ConnectionError as RequestsConnectionError,
)
from requests.exceptions import (
    HTTPError,
    Timeout,
)
from shapely.geometry import MultiPoint, Point
from shapely.geometry.polygon import Polygon

from airport_lookup import get_airport_by_icao, get_closest_airport
from calculate_headings import (
    calculate_cardinal,
    calculate_deg_change,
    calculate_from_bearing,
)
from cnf_parser_ext import ConfigParserExt
from constants import Flags, ImageTypes, NavModes, normalize_nav_modes
from db import (
    add_flight,
    get_aircraft_reg_by_icao,
    update_flight,
)
from flight_static_maps.data_adapters import pn_adapter
from flight_static_maps.map import generate_map
from fuel_calc import fuel_calculation, fuel_message
from geo import get_circle_perimeter_coords
from notification_manager import NotificationManager
from providers import Providers
from utils import cleanup_images, set_dyn_title

try:
    import lookup_route  # noqa: F401

    ENABLE_ROUTE_LOOKUP = True
except ImportError:
    ENABLE_ROUTE_LOOKUP = False

logger = logging.getLogger(__name__)

main_config = ConfigParserExt()
main_config.read("./configs/mainconf.ini")


class Plane:
    def __init__(self, icao, config):
        """Initializes a plane object from its config file and given icao."""
        self.icao = icao.lower()
        self.active_icao = self.icao
        self.pia_icao = None
        if config.has_option("DATA", "PIA_ICAO"):
            self.pia_icao = config.get("DATA", "PIA_ICAO").lower()
        self.callsign = None
        self.config = config
        self.overrides = {}
        if self.config.has_option("DATA", "OVERRIDE_REG"):
            self.reg = self.config.get("DATA", "OVERRIDE_REG")
            self.overrides["reg"] = self.reg
        else:
            self.reg = None
        if self.config.has_option("DATA", "OVERRIDE_ICAO_TYPE"):
            self.type = self.config.get("DATA", "OVERRIDE_ICAO_TYPE")
            self.overrides["type"] = self.type
        else:
            self.type = None
        if self.config.has_option("DATA", "OVERRIDE_ICAO_TYPE"):
            self.overrides["typelong"] = self.config.get("DATA", "OVERRIDE_TYPELONG")
        if self.config.has_option("DATA", "OVERRIDE_OWNER"):
            self.overrides["ownop"] = self.config.get("DATA", "OVERRIDE_OWNER")
        if self.config.has_option("DATA", "CONCEAL_AC_ID"):
            self.conceal_ac_id = self.config.getboolean("DATA", "CONCEAL_AC_ID")
        else:
            self.conceal_ac_id = False
        if self.config.has_option("DATA", "CONCEAL_PIA"):
            self.conceal_pia = self.config.getboolean("DATA", "CONCEAL_PIA")
        else:
            self.conceal_pia = False
        self.alt_ft = None
        self.below_desired_ft = None
        self.last_below_desired_ft = None
        self.feeding = None
        self.last_feeding = None
        self.last_on_ground = None
        self.on_ground = None
        self.longitude = None
        self.latitude = None
        self.takeoff_time = None
        self.last_latitude = None
        self.last_longitude = None
        self.last_pos_datetime = None
        self.landing_plausible = False
        self.nav_modes = None
        self.last_nav_modes = None
        self.speed = None
        self.recent_ra_types = {}
        self.db_flags = None
        self.sel_nav_alt = None
        self.last_sel_alt = None
        self.squawk = None
        self.emergency_already_triggered = None
        self.last_emergency = None
        self.recheck_route_time = None
        self.known_to_airport = None
        self.track = None
        self.last_track = None
        self.circle_history = None
        self.traces = []
        self.nearest_from_airport = None
        self.db_flight_id = None
        self.pia_active = None
        self.flags = []
        self.category = None
        self.category = None
        if self.config.has_section("X") and self.config.getboolean("X", "ENABLE"):
            pass  # X client moved to NotificationManager
        self.notification_manager = NotificationManager(self.config, main_config)
        if self.config.has_option("DATA", "DATA_LOSS_MINS"):
            self.data_loss_mins = self.config.getint("DATA", "DATA_LOSS_MINS")
        else:
            self.data_loss_mins = main_config.getint("DATA", "DATA_LOSS_MINS")

    def run_readsb(self, ac_dict, pia):
        # Parse READSB Vector
        self.print_header()
        self.pia_active = pia
        try:
            self.active_icao = ac_dict["hex"].upper()
            self.latitude = float(ac_dict["lat"])
            self.longitude = float(ac_dict["lon"])
            if "r" in ac_dict:
                self.reg = ac_dict["r"]
            self.speed = ac_dict.get("gs")
            if "t" in ac_dict:
                self.type = ac_dict["t"]
            if "category" in ac_dict:
                self.category = ac_dict["category"]
            if "type" in ac_dict:
                self.data_source = ac_dict["type"]
            if ac_dict["alt_baro"] != "ground":
                self.alt_ft = int(ac_dict["alt_baro"])
                self.on_ground = False
            elif ac_dict["alt_baro"] == "ground":
                self.alt_ft = 0
                self.on_ground = True
            if ac_dict.get("flight"):
                self.callsign = ac_dict.get("flight").strip()
            else:
                self.callsign = None
            if ac_dict.get("dbFlags"):
                self.flags = []
                db_flags = ac_dict["dbFlags"]
                if bool(db_flags & 1):
                    self.flags.append(Flags.MILITARY)
                if bool(db_flags & 2):
                    self.flags.append(Flags.INTRESTING)
                if bool(db_flags & 4):
                    self.flags.append(Flags.PIA)
                if bool(db_flags & 8):
                    self.flags.append(Flags.LADD)

            if "nav_modes" in ac_dict:
                self.nav_modes = normalize_nav_modes(ac_dict["nav_modes"])
            self.squawk = ac_dict.get("squawk")
            if "track" in ac_dict:
                self.track = ac_dict["track"]
            if "nav_altitude_fms" in ac_dict:
                self.sel_nav_alt = ac_dict["nav_altitude_fms"]
            elif "nav_altitude_mcp" in ac_dict:
                self.sel_nav_alt = ac_dict["nav_altitude_mcp"]
            else:
                self.sel_nav_alt = None

            # Create last seen timestamp from how long ago in secs a pos was rec
            self.last_pos_datetime = datetime.now() - timedelta(
                seconds=ac_dict["seen_pos"]
            )
        except (ValueError, KeyError) as e:
            logger.warning("Got data but some data is invalid!")
            logger.warning(e)
            logger.warning(
                f"{Fore.YELLOW}READSB Sourced Data: {ac_dict}{Style.RESET_ALL}"
            )
            self.print_footer()
        else:
            # Error Handling for bad data, sometimes it would seem to be ADSB Decode error
            if (not self.on_ground) and self.speed and self.speed <= 10:
                logger.debug("Not running check, appears to be bad ADSB Decode")
            else:
                self.feeding = True
                self.run_check()

    def __str__(self):
        if self.last_pos_datetime is not None:
            time_since_contact = self.get_time_since(self.last_pos_datetime)

        output_parts = [
            f"{Fore.CYAN}ICAO:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{self.active_icao}{Style.RESET_ALL}"
            + (f" {Fore.YELLOW}(PIA){Style.RESET_ALL}" if self.pia_active else "")
        ]

        if self.callsign:
            output_parts.append(
                f"{Fore.CYAN}Call:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{self.callsign.strip()}{Style.RESET_ALL}"
            )

        if self.reg:
            output_parts.append(
                f"{Fore.CYAN}Reg:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{self.reg}{Style.RESET_ALL}"
            )

        if self.alt_ft is not None:
            output_parts.append(
                f"{Fore.CYAN}Alt:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{self.alt_ft:,}ft{Style.RESET_ALL}"
            )

        if self.on_ground is not None:
            output_parts.append(
                f"{Fore.CYAN}Gnd:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{self.on_ground}{Style.RESET_ALL}"
            )

        if self.last_pos_datetime:
            output_parts.append(
                f"""{Fore.CYAN}Seen:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{str(time_since_contact).split(".")[0]}{Style.RESET_ALL}"""
            )

        output_parts.append(
            f"{Fore.CYAN}Points:{Style.RESET_ALL} {Fore.LIGHTGREEN_EX}{len(self.traces)}{Style.RESET_ALL}"
        )

        return " | ".join(output_parts)

    def print_header(self):
        logger.info("Processing %s ICAO: %s", self.config.filepath, self.active_icao)

    def print_footer(self):
        logger.info("Processing Complete %s", self.config.filepath)

    def get_time_since(self, datetime_obj):
        if datetime_obj is not None:
            time_since = datetime.now() - datetime_obj
        else:
            time_since = None
        return time_since

    def route_info(self):
        from lookup_route import clean_data, lookup_route

        def route_format(extra_route_info, type):
            to_airport = get_airport_by_icao(self.known_to_airport)
            if to_airport:
                code = (
                    to_airport["iata_code"]
                    if to_airport["iata_code"] != ""
                    else to_airport["icao_code"]
                )
                airport_text = f"""{code}, {to_airport["name"]}"""
            else:
                airport_text = f"{self.known_to_airport}"
            if "time_to" in extra_route_info.keys() and type != "divert":
                arrival_rel = f"""in ~{extra_route_info["time_to"]}"""
            else:
                arrival_rel = None
            if self.known_to_airport != self.nearest_from_airport:
                if type == "inital":
                    header = "Going to"
                elif type == "change":
                    header = "Now going to"
                elif type == "divert":
                    header = "Now diverting to"
                if to_airport:
                    area = f"""{to_airport["municipality"]}, {to_airport["region"]}, {to_airport["iso_country"]}"""
                else:
                    area = ""
                route_to = f"{header} {area} ({airport_text})" + (
                    f" arriving {arrival_rel}" if arrival_rel is not None else ""
                )
            else:
                if type == "inital":
                    header = "Will be returning to"
                elif type == "change":
                    header = "Now returning to"
                elif type == "divert":
                    header = "Now diverting back to"
                route_to = f"{header} {airport_text}" + (
                    f" {arrival_rel}" if arrival_rel is not None else ""
                )
            return route_to

        if hasattr(self, "type"):
            extra_route_info = clean_data(
                lookup_route(
                    self.reg, (self.latitude, self.longitude), self.type, self.alt_ft
                )
            )
        else:
            extra_route_info = None
        route_to = None
        if extra_route_info is None:
            pass
        elif extra_route_info is not None:
            # Diversion
            if "divert_icao" in extra_route_info.keys():
                if self.known_to_airport != extra_route_info["divert_icao"]:
                    self.known_to_airport = extra_route_info["divert_icao"]
                    route_to = route_format(extra_route_info, "divert")
            # Destination
            elif "dest_icao" in extra_route_info.keys():
                # Inital Destination Found
                if self.known_to_airport is None:
                    self.known_to_airport = extra_route_info["dest_icao"]
                    route_to = route_format(extra_route_info, "inital")
                # Destination Change
                elif self.known_to_airport != extra_route_info["dest_icao"]:
                    self.known_to_airport = extra_route_info["dest_icao"]
                    route_to = route_format(extra_route_info, "change")

        return route_to

    def run_empty(self):
        self.print_header()
        self.feeding = False
        self.run_check()

    def add_trace(self):
        if self.latitude and self.longitude and self.alt_ft is not None:
            last_trace = self.traces[-1] if len(self.traces) >= 1 else None
            # Only add trace if none exist or if new telemetry coordinates are not the same as last coordinates
            if (
                last_trace
                and self.latitude != last_trace[1]
                and self.longitude != last_trace[2]
            ) or not last_trace:
                trace = (
                    time.time(),
                    self.latitude,
                    self.longitude,
                    self.alt_ft,
                    self.on_ground,
                )
                self.traces.append(trace)

    def expire_traces(self):
        if self.traces:
            for trace in self.traces:
                trace_timestramp = trace[0]
                if (
                    datetime.now() - datetime.fromtimestamp(trace_timestramp)
                ).total_seconds() >= 30 * 60:
                    logger.info("Main Trace Expire, removed")
                    self.traces.remove(trace)

    def get_flags(self):
        flags = []
        if self.pia_active:
            flags.append(Flags.PIA)

    def run_check(self):
        """Runs a check of a plane module to see if its landed or takenoff using plane data, and takes action if so."""

        self.add_trace()
        logger.info(self)
        if self.last_pos_datetime is not None:
            time_since_contact = self.get_time_since(self.last_pos_datetime)
        # Check if below desire ft
        desired_ft = 15000
        if self.alt_ft is None or self.alt_ft > desired_ft:
            self.below_desired_ft = False
        elif self.alt_ft < desired_ft:
            self.below_desired_ft = True
        # Check if tookoff
        if self.below_desired_ft and self.on_ground is False:
            if self.last_on_ground:
                self.tookoff = True
                trigger_type = "no longer on ground"
                type_header = "Took off from"
            elif (
                self.last_feeding is False
                and self.feeding
                and not self.landing_plausible
            ):
                nearest_airport_dict = get_closest_airport(
                    self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES")
                )
                if nearest_airport_dict["elevation_ft"]:
                    alt_above_airport = self.alt_ft - int(
                        nearest_airport_dict["elevation_ft"]
                    )
                    logger.info("AGL nearest airport: %s", alt_above_airport)
                else:
                    alt_above_airport = None
                if (
                    alt_above_airport is not None and alt_above_airport <= 10000
                ) or self.alt_ft <= 15000:
                    self.tookoff = True
                    trigger_type = "data acquisition"
                    type_header = "Took off near"
            else:
                self.tookoff = False
        else:
            self.tookoff = False

        # Check if Landed
        if (
            self.on_ground
            and self.last_on_ground is False
            and self.last_below_desired_ft
        ):
            self.landed = True
            trigger_type = "now on ground"
            type_header = "Landed in"
            self.landing_plausible = False
        # Set status for landing plausible
        elif (
            self.below_desired_ft
            and self.last_feeding
            and self.feeding is False
            and self.last_on_ground is False
        ):
            self.landing_plausible = True
            logger.info(
                "Near landing conditions, if contiuned data loss for configured time, and  if under 10k AGL landing true"
            )

        elif (
            self.landing_plausible
            and self.feeding is False
            and time_since_contact.total_seconds() >= (self.data_loss_mins * 60)
        ):
            nearest_airport_dict = get_closest_airport(
                self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES")
            )
            if nearest_airport_dict["elevation_ft"]:
                alt_above_airport = self.alt_ft - int(
                    nearest_airport_dict["elevation_ft"]
                )
                logger.info("AGL nearest airport: %s", alt_above_airport)
            else:
                alt_above_airport = None
            if (
                alt_above_airport is not None and alt_above_airport <= 10000
            ) or self.alt_ft <= 15000:
                self.landing_plausible = False
                self.on_ground = None
                self.landed = True
                trigger_type = "data loss"
                type_header = "Landed near"
            else:
                logger.info("Alt greater then 10k AGL")
                self.landing_plausible = False
                self.on_ground = None
        else:
            self.landed = False

        if self.landed:
            logger.info("Landed by %s", trigger_type)
        if self.tookoff:
            logger.info("Tookoff by %s", trigger_type)
        # Find nearest airport, and location
        if self.landed or self.tookoff:
            if "nearest_airport_dict" in globals():
                pass  # Airport already set
            elif trigger_type in ["now on ground", "data acquisition", "data loss"]:
                nearest_airport_dict = get_closest_airport(
                    self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES")
                )
            elif trigger_type == "no longer on ground":
                nearest_airport_dict = get_closest_airport(
                    self.last_latitude,
                    self.last_longitude,
                    self.config.get("AIRPORT", "TYPES"),
                )
            # Convert dictionary keys to sep variables
            country = nearest_airport_dict["country"]
            state = nearest_airport_dict["region"]
            city = nearest_airport_dict["municipality"]

            last_loc = None
            location_string = ""
            for loc in [city, state, country]:
                if not last_loc:
                    location_string = loc
                elif loc and loc != last_loc:
                    location_string += f", {loc}"
                last_loc = loc

            logger.info(
                Fore.GREEN
                + "Country: "
                + country
                + " State: "
                + state
                + " City: "
                + city
                + Style.RESET_ALL
            )
        # Title
        title = self.config.get_title("DATA")
        self.title = set_dyn_title(title, self.callsign, self.reg, self.active_icao)
        # Takeoff and Land Notification
        if self.tookoff or self.landed:
            route_to = None
            second_message = None
            if self.tookoff:
                self.takeoff_time = datetime.now(UTC)
                confirmed_takeoff = (
                    True if trigger_type == "no longer on ground" else False
                )
                self.db_flight_id = add_flight(
                    self.reg,
                    self.icao,
                    self.callsign,
                    nearest_airport_dict["icao_code"],
                    confirmed_takeoff,
                    self.takeoff_time,
                )
                landed_time_msg = None
                # Proprietary Route Lookup
                if ENABLE_ROUTE_LOOKUP and Flags.MILITARY not in self.flags:
                    self.nearest_from_airport = nearest_airport_dict["icao_code"]
                    route_to = self.route_info()
                    if route_to is None:
                        self.recheck_route_time = 1
                    else:
                        self.recheck_route_time = 10
            elif self.landed and self.takeoff_time is not None:
                landed_time = datetime.now(UTC) - self.takeoff_time
                if trigger_type == "data loss":
                    landed_time -= timedelta(seconds=time_since_contact.total_seconds())
                hours, remainder = divmod(landed_time.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                min_syntax = "min"
                if hours > 0:
                    hour_syntax = "h"
                    landed_time_msg = f"Apx. flt. time {int(hours)} {hour_syntax}" + (
                        f" {int(minutes)} {min_syntax}. " if minutes > 0 else "."
                    )
                else:
                    landed_time_msg = f"Apx. flt. time {int(minutes)} {min_syntax}."
                confirmed_landing = True if trigger_type == "now on ground" else False
                update_flight(
                    self.db_flight_id,
                    nearest_airport_dict["icao_code"],
                    confirmed_landing,
                    datetime.now(UTC),
                )
                # Start Secondary Output Creation, Miles and Fuel
                if (
                    nearest_airport_dict is not None
                    and self.nearest_from_airport is not None
                    and nearest_airport_dict["icao"] != self.nearest_from_airport
                ):
                    landed_airport = nearest_airport_dict
                    nearest_from_airport = get_airport_by_icao(
                        self.nearest_from_airport
                    )
                    from_coord = (
                        nearest_from_airport["lat"],
                        nearest_from_airport["lon"],
                    )
                    to_coord = (landed_airport["lat"], landed_airport["lon"])
                    distance_mi = float(geodesic(from_coord, to_coord).mi)
                    distance_nm = distance_mi / 1.150779448
                    second_message = f"""{f"{round(distance_mi):,}"} mile ({f"{round(distance_nm):,}"} NM) flight from {nearest_from_airport["iata_code"] if nearest_from_airport["iata_code"] != "" else nearest_from_airport["ident"]} to {nearest_airport_dict["iata_code"] if nearest_airport_dict["iata_code"] != "" else nearest_airport_dict["ident"]}"""
                if self.type is not None:
                    logger.info("Running fuel info calc")
                    flight_time_min = landed_time.total_seconds() / 60
                    fuel_info = fuel_calculation(self.type, flight_time_min)
                    if fuel_info is not None:
                        if second_message:
                            second_message += f"\n{fuel_message(fuel_info)}"
                        else:
                            second_message = f"{fuel_message(fuel_info)}"
                self.db_flight_id = None
                self.takeoff_time = None
            elif self.landed:
                landed_time_msg = None
                landed_time = None

            message = (
                (f"{type_header} {location_string}.")
                + ("" if route_to is None else f" {route_to}.")
                + ((f" {landed_time_msg}") if landed_time_msg is not None else "")
            )
            logger.info(message)

            if (
                self.config.getboolean("TELEGRAM", "ENABLE")
                or self.config.getboolean("MASTODON", "ENABLE")
                or self.config.getboolean("DISCORD", "ENABLE")
                or self.config.getboolean("X", "ENABLE")
                or self.config.getboolean("META", "ENABLE")
                or self.config.getboolean("BLUESKY", "ENABLE")
                or self.config.getboolean("NOSTR", "ENABLE")
                or self.config.getboolean("THREADS", "ENABLE")
            ):
                # Map generation
                image_type = ImageTypes.LANDED if self.landed else ImageTypes.TAKEOFF
                timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M")
                db_id = f"{self.db_flight_id}_" if self.db_flight_id else ""
                map_img_filename = os.path.join(
                    tempfile.gettempdir(),
                    "plane-notify",
                    "imgs",
                    f"{db_id}{self.active_icao.upper()}_{image_type}_{timestamp}_map",
                )
                logger.debug(map_img_filename)
                if main_config.get("MAP", "OPTION") == "fsm":
                    info = pn_adapter(self)
                    info["nearest_airport"] = nearest_airport_dict

                    generate_map(
                        map_img_filename,
                        self.traces,
                        info,
                        True,
                        blur_identity=self.config.getboolean("DATA", "BLUR_ID"),
                    )
                else:
                    raise ValueError("Map option not set correctly in this planes conf")
                # alt_text = f"Reg: {self.reg} On Ground: {str(self.on_ground)} Alt: {str(self.alt_ft)} Last Contact: {str(time_since_contact)} Trigger: {trigger_type}"
            else:
                map_img_filename = None

            # Notifications

            self.notification_manager.post_to_all(
                message=message,
                title=self.title,
                image_path=map_img_filename + ".png",
            )
            if second_message:
                self.notification_manager.post_to_all(
                    message=second_message,
                    title=self.title,
                    image_path=None,
                    is_reply=True,
                )
            # Cleanup Remove Image
            cleanup_images(map_img_filename)
            # Cleanup
            if self.landed:
                self.traces.clear()
                self.notification_manager.reset_state()
                self.recheck_route_time = None
                self.known_to_airport = None
                self.nearest_from_airport = None
        # Recheck Proprietary Route Info.
        if (
            self.takeoff_time
            and self.recheck_route_time
            and (datetime.now(UTC) - self.takeoff_time).total_seconds()
            > 60 * self.recheck_route_time
        ):
            self.recheck_route_time += 10
            route_to = self.route_info()
            if route_to is not None:
                logger.info(route_to)
                self.notification_manager.set_one_time_exclusive(
                    [Providers.TELEGRAM, Providers.DISCORD, Providers.X]
                )
                self.notification_manager.post_to_all(
                    message=route_to, title=self.title, is_reply=True, image_path=None
                )

        if self.circle_history is not None:
            # Expires traces for circles
            if self.circle_history["traces"] != []:
                for trace in self.circle_history["traces"]:
                    if (
                        datetime.now() - datetime.fromtimestamp(trace[0])
                    ).total_seconds() >= 20 * 60:
                        logger.info("Trace Expire, removed")
                        self.circle_history["traces"].remove(trace)
            # Expire touchngo
            if (
                "touchngo" in self.circle_history.keys()
                and (
                    datetime.now()
                    - datetime.fromtimestamp(self.circle_history["touchngo"])
                ).total_seconds()
                >= 10 * 60
            ):
                self.circle_history.pop("touchngo")
        if self.feeding:
            # Squawks
            emergency_squawks = {
                "7500": "Hijacking",
                "7600": "Radio Failure",
                "7700": "General Emergency",
            }
            seen = datetime.now() - self.last_pos_datetime
            # Only run check if emergency data previously set
            if self.last_emergency is not None and not self.emergency_already_triggered:
                time_since_org_emer = datetime.now() - self.last_emergency[0]
                # Checks times to see x time and still same squawk
                if (
                    time_since_org_emer.total_seconds() >= 60
                    and self.last_emergency[1] == self.squawk
                    and seen.total_seconds() <= 60
                ):
                    self.emergency_already_triggered = True
                    squawk_message = (
                        f"{self.title} Squawking {self.last_emergency[1]} {emergency_squawks[self.squawk]}"
                    ).strip()
                    logger.info(squawk_message)
                    # Map generation
                    image_type = ImageTypes.EMERGENCY
                    timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M")
                    map_img_filename = os.path.join(
                        tempfile.gettempdir(),
                        "plane-notify",
                        "imgs",
                        f"{self.active_icao.upper()}_{image_type}_{timestamp}_map",
                    )
                    if main_config.get("MAP", "OPTION") == "fsm":
                        info = pn_adapter(self)
                        info["nearest_airport"] = None
                        generate_map(
                            map_img_filename,
                            self.traces,
                            info,
                            True,
                            blur_identity=self.config.getboolean("DATA", "BLUR_ID"),
                        )
                    self.notification_manager.set_one_time_exclusive(
                        [Providers.DISCORD]
                    )
                    self.notification_manager.post_to_all(
                        message=squawk_message,
                        title=self.title,
                        image_path=map_img_filename + ".png",
                    )
                    os.remove(map_img_filename + ".png")
            # Realizes first time seeing emergency, stores time and type
            elif (
                self.squawk in emergency_squawks.keys()
                and not self.emergency_already_triggered
                and not self.on_ground
            ):
                logger.info(
                    f"Emergency {self.squawk} detected storing code and time and waiting to trigger"
                )
                self.last_emergency = (self.last_pos_datetime, self.squawk)
            elif (
                self.squawk not in emergency_squawks.keys()
                and self.emergency_already_triggered
            ):
                self.emergency_already_triggered = None

            # Nav Modes Notifications
            if self.nav_modes is not None and self.last_nav_modes is not None:
                for mode in self.nav_modes:
                    if mode not in self.last_nav_modes:
                        logger.info("%s enabled", mode)
                        message = f"{mode} mode enabled."
                        if mode == NavModes.APPROACH:
                            image_type = ImageTypes.APPROACH
                            timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M")
                            map_img_filename = os.path.join(
                                tempfile.gettempdir(),
                                "plane-notify",
                                "imgs",
                                f"{self.active_icao.upper()}_{image_type}_{timestamp}_map",
                            )
                            info = pn_adapter(self)
                            info["nearest_airport"] = None
                            generate_map(
                                map_img_filename,
                                self.traces,
                                info,
                                True,
                                blur_identity=self.config.getboolean("DATA", "BLUR_ID"),
                            )
                            self.notification_manager.set_one_time_exclusive(
                                [Providers.DISCORD]
                            )
                            self.notification_manager.post_to_all(
                                message=message,
                                title=self.title,
                                image_path=map_img_filename + ".png",
                            )
                            cleanup_images(map_img_filename)
                        # elif mode in ["Althold", "VNAV", "LNAV"] and self.sel_nav_alt != None:
                        #    discord.post((dis_message + ", Sel Alt. " + str(self.sel_nav_alt) + ", Current Alt. " + str(self.alt_ft)), self.config)
                        else:
                            self.notification_manager.set_one_time_exclusive(
                                [Providers.DISCORD]
                            )
                            self.notification_manager.post_to_all(
                                message=message,
                                title=self.title,
                                image_path=None,
                            )
            # Selected Altitude
            if (
                self.sel_nav_alt is not None
                and self.last_sel_alt is not None
                and self.last_sel_alt != self.sel_nav_alt
            ):
                logger.info("Nav altitude is now %s", self.sel_nav_alt)
                message = " Sel.  alt. " + str(f"{self.sel_nav_alt:,} ft")
                self.notification_manager.set_one_time_exclusive([Providers.DISCORD])
                self.notification_manager.post_to_all(
                    message=message,
                    title=self.title,
                    image_path=None,
                )
            # Circling
            if self.last_track is not None:
                if self.circle_history is None:
                    self.circle_history = {"traces": [], "triggered": False}
                # Add touchngo
                if self.on_ground or self.alt_ft <= 500:
                    self.circle_history["touchngo"] = time.time()
                # Add a Trace
                if self.on_ground is False:
                    track_change = calculate_deg_change(self.track, self.last_track)
                    track_change = round(track_change, 3)
                    if self.latitude is not None and self.longitude is not None:
                        self.circle_history["traces"].append(
                            (time.time(), self.latitude, self.longitude, track_change)
                        )

                total_change = 0
                coords = []
                for trace in self.circle_history["traces"]:
                    total_change += float(trace[3])
                    coords.append((float(trace[1]), float(trace[2])))

                logger.info("Total Bearing Change %s", round(total_change, 3))
                # Check Centroid when Bearing change meets req
                if (
                    abs(total_change) >= 720
                    and self.circle_history["triggered"] is False
                ):
                    logger.info("Circling Bearing Change Met")
                    aircraft_coords = (self.latitude, self.longitude)
                    points = MultiPoint(coords)
                    cent = (
                        points.centroid
                    )  # True centroid, not necessarily an existing point
                    # rp =  (points.representative_point()) #A represenative point, not centroid,
                    logger.debug(cent)
                    # print(rp)
                    distance_to_centroid = round(
                        geodesic(aircraft_coords, cent.coords).mi, 2
                    )
                    logger.info(
                        f"Distance to centroid of circling coordinates {distance_to_centroid} miles"
                    )
                    if distance_to_centroid <= 15:
                        logger.info("Within 15 miles of centroid, CIRCLING")
                        # Finds Nearest Airport
                        nearest_airport_dict = get_closest_airport(
                            self.latitude,
                            self.longitude,
                            self.config.get("AIRPORT", "TYPES"),
                        )
                        from_bearing = calculate_from_bearing(
                            (
                                float(nearest_airport_dict["lat"]),
                                float(nearest_airport_dict["lon"]),
                            ),
                            (self.latitude, self.longitude),
                        )
                        cardinal = calculate_cardinal(from_bearing)
                        # Finds Nearest TFR or in TFR

                        closest_tfr = None
                        in_tfr = None
                        if main_config.getboolean("TFRS", "ENABLE"):
                            tfr_url = main_config.get("TFRS", "URL")
                            try:
                                response = requests.get(tfr_url, timeout=15)
                                response.raise_for_status()
                                tfrs = json.loads(response.text)
                            except (
                                HTTPError,
                                Timeout,
                                RequestsConnectionError,
                                json.decoder.JSONDecodeError,
                            ) as err:
                                logger.error("Error with TFRS: %s", err)
                                tfrs = None
                            else:
                                for tfr in tfrs:
                                    if in_tfr is not None:
                                        break
                                    elif (
                                        tfr["details"] is not None
                                        and "shapes" in tfr["details"].keys()
                                    ):
                                        for index, shape in enumerate(
                                            tfr["details"]["shapes"]
                                        ):
                                            shape["txtName"] = f"shape_{index}"
                                            polygon = None
                                            if shape["type"] == "poly":
                                                points = shape["points"]
                                            elif shape["type"] == "circle":
                                                radius_km = (
                                                    float(shape["radius"]) * 1.852
                                                )
                                                points = get_circle_perimeter_coords(
                                                    shape["lat"],
                                                    shape["lon"],
                                                    radius_km,
                                                )
                                            elif shape["type"] in [
                                                "polyarc",
                                                "polyexclude",
                                                "linebuffer",
                                            ]:
                                                points = shape["all_points"]
                                            aircraft_location = Point(
                                                self.latitude, self.longitude
                                            )
                                            if polygon is None:
                                                if len(points) < 4:
                                                    raise ValueError(
                                                        "Less than 4 points occured on NOTAM ->",
                                                        tfr["NOTAM"],
                                                    )
                                                polygon = Polygon(points)
                                            if polygon.contains(aircraft_location):
                                                in_tfr = {
                                                    "info": tfr,
                                                    "closest_shape_name": shape[
                                                        "txtName"
                                                    ],
                                                }
                                                break
                                            else:
                                                point_dists = []
                                                for point in points:
                                                    point = tuple(point)
                                                    point_dists.append(
                                                        float(
                                                            geodesic(
                                                                (
                                                                    self.latitude,
                                                                    self.longitude,
                                                                ),
                                                                point,
                                                            ).mi
                                                        )
                                                    )
                                                distance = min(point_dists)
                                                if closest_tfr is None:
                                                    closest_tfr = {
                                                        "info": tfr,
                                                        "closest_shape_name": shape[
                                                            "txtName"
                                                        ],
                                                        "distance": round(distance),
                                                    }
                                                elif distance < closest_tfr["distance"]:
                                                    closest_tfr = {
                                                        "info": tfr,
                                                        "closest_shape_name": shape[
                                                            "txtName"
                                                        ],
                                                        "distance": round(distance),
                                                    }
                                if in_tfr is not None:
                                    for shape in in_tfr["info"]["details"]["shapes"]:
                                        if (
                                            shape["txtName"]
                                            == in_tfr["closest_shape_name"]
                                        ):
                                            val_dist_ver_upper, val_dist_ver_lower = (
                                                int(shape["valDistVerUpper"]),
                                                int(shape["valDistVerLower"]),
                                            )
                                            logger.info(
                                                f"In TFR based off location checking alt next {in_tfr}"
                                            )
                                            break
                                    if not (
                                        self.alt_ft >= val_dist_ver_lower
                                        and self.alt_ft <= val_dist_ver_upper
                                    ):
                                        if self.alt_ft > val_dist_ver_upper:
                                            in_tfr["context"] = "above"
                                        elif self.alt_ft < val_dist_ver_lower:
                                            in_tfr["context"] = "below"
                                        logger.info(
                                            f"But not in alt of TFR {in_tfr['context']}"
                                        )

                                if in_tfr is None:
                                    logger.info("Closest TFR %s", closest_tfr)
                            # Generate Map
                            context = staticmaps.Context()
                            context.set_tile_provider(staticmaps.tile_provider_OSM)
                            if tfrs:
                                if in_tfr is not None:
                                    shapes = in_tfr["info"]["details"]["shapes"]
                                else:
                                    shapes = closest_tfr["info"]["details"]["shapes"]

                                def draw_poly(context, pairs):
                                    pairs.append(pairs[0])
                                    context.add_object(
                                        staticmaps.Area(
                                            [
                                                staticmaps.create_latlng(lat, lng)
                                                for lat, lng in pairs
                                            ],
                                            fill_color=staticmaps.parse_color(
                                                "#FF000033"
                                            ),
                                            width=2,
                                            color=staticmaps.parse_color("#8B0000"),
                                        )
                                    )
                                    return context

                                for shape in shapes:
                                    if shape["type"] == "poly":
                                        pairs = shape["points"]
                                        context = draw_poly(context, pairs)
                                    elif (
                                        shape["type"] == "polyarc"
                                        or shape["type"] == "polyexclude"
                                    ):
                                        pairs = shape["all_points"]
                                        context = draw_poly(context, pairs)
                                    elif shape["type"] == "circle":
                                        center = [shape["lat"], shape["lon"]]
                                        center1 = staticmaps.create_latlng(
                                            center[0], center[1]
                                        )
                                        context.add_object(
                                            staticmaps.Circle(
                                                center1,
                                                (float(shape["radius"]) * 1.852),
                                                fill_color=staticmaps.parse_color(
                                                    "#FF000033"
                                                ),
                                                color=staticmaps.parse_color("#8B0000"),
                                                width=2,
                                            )
                                        )
                                        context.add_object(
                                            staticmaps.Marker(
                                                center1, color=staticmaps.RED
                                            )
                                        )
                        image_type = ImageTypes.CIRCLING
                        timestamp = datetime.now(UTC).strftime("%Y-%m-%d_%H-%M")
                        map_img_filename = os.path.join(
                            tempfile.gettempdir(),
                            "plane-notify",
                            "imgs",
                            f"{self.active_icao.upper()}_{image_type}_{timestamp}_map",
                        )
                        if main_config.get("MAP", "OPTION") == "fsm":
                            info = pn_adapter(self)
                            info["nearest_airport"] = nearest_airport_dict
                            generate_map(
                                map_img_filename,
                                self.traces,
                                info,
                                True,
                                blur_identity=self.config.getboolean("DATA", "BLUR_ID"),
                            )

                        if nearest_airport_dict["distance_mi"] < 3:
                            if "touchngo" in self.circle_history.keys():
                                message = f"""Doing touch and goes at {nearest_airport_dict["icao_code"]}"""
                            else:
                                message = f"""Circling over {nearest_airport_dict["icao_code"]} at {self.alt_ft}ft."""
                        else:
                            message = f"""Circling {round(nearest_airport_dict["distance_mi"], 2)}mi {cardinal} of {nearest_airport_dict["icao_code"]}, {nearest_airport_dict["name"]} at {self.alt_ft}ft. """
                        tfr_map_filename = None

                        def tfr_image(context, aircraft_coords):
                            heading = self.track
                            heading *= -1
                            im = Image.open("./dependencies/ac.png")
                            im_rotate = im.rotate(heading, resample=Image.BICUBIC)
                            rotated_file = f"{tempfile.gettempdir()}/rotated_ac.png"
                            im_rotate.save(rotated_file)
                            pos = staticmaps.create_latlng(
                                aircraft_coords[0], aircraft_coords[1]
                            )
                            marker = staticmaps.ImageMarker(
                                pos, rotated_file, origin_x=35, origin_y=35
                            )
                            context.add_object(marker)
                            image = context.render_cairo(1000, 1000)
                            os.remove(rotated_file)
                            tfr_map_filename = (
                                f"{tempfile.gettempdir()}/{self.active_icao}_TFR_.png"
                            )
                            image.write_to_png(tfr_map_filename)
                            return tfr_map_filename

                        if in_tfr:
                            wording_context = (
                                "Inside"
                                if "context" not in in_tfr.keys()
                                else "Above"
                                if in_tfr["context"] == "above"
                                else "Below"
                                if in_tfr["context"] == "below"
                                else "Near"
                            )
                            message += f""" {wording_context} TFR {in_tfr["info"]["NOTAM"]}, a TFR for {in_tfr["info"]["Type"].title()}"""
                            tfr_map_filename = tfr_image(
                                context, (self.latitude, self.longitude)
                            )
                        elif (
                            in_tfr is None
                            and closest_tfr is not None
                            and "distance" in closest_tfr.keys()
                            and closest_tfr["distance"] <= 20
                        ):
                            message += f""" {closest_tfr["distance"]} miles from TFR {closest_tfr["info"]["NOTAM"]}, a TFR for {closest_tfr["info"]["Type"]}"""
                            tfr_map_filename = tfr_image(
                                context, (self.latitude, self.longitude)
                            )
                        elif (
                            in_tfr is None
                            and closest_tfr is not None
                            and "distance" not in closest_tfr.keys()
                        ):
                            message += f""" near TFR {closest_tfr["info"]["NOTAM"]}, a TFR for {closest_tfr["info"]["Type"]}"""
                            raise Exception(message)
                        logger.info(message)
                        # Notifications
                        self.notification_manager.post_to_all(
                            message=message,
                            title=self.title,
                            image_path=map_img_filename + ".png",
                            reg=self.reg,
                        )
                        cleanup_images(map_img_filename)
                        if tfr_map_filename:
                            os.remove(tfr_map_filename)
                        self.circle_history["triggered"] = True
                elif abs(total_change) <= 360 and self.circle_history["triggered"]:
                    logger.info("No Longer Circling, trigger cleared")
                    self.circle_history["triggered"] = False
            # #Power Up
            # if self.last_feeding == False and self.speed == 0 and self.on_ground:
            #     if self.config.getboolean('DISCORD', 'ENABLE'):
            #         dis_message = (self.dis_title + "Powered Up").strip()
            #         discord.post(dis_message, self.config)

        # Set Variables to compare to next check
        self.last_track = self.track
        self.last_feeding = self.feeding
        self.last_on_ground = self.on_ground
        self.last_below_desired_ft = self.below_desired_ft
        self.last_longitude = self.longitude
        self.last_latitude = self.latitude
        self.last_nav_modes = self.nav_modes
        self.last_sel_alt = self.sel_nav_alt

        self.expire_traces()

        if self.takeoff_time is not None:
            elapsed_time = datetime.now(UTC) - self.takeoff_time
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            logger.info(
                f"Time Since Take off  {int(hours)} Hours : {int(minutes)} Mins : {int(seconds)} Secs"
            )
        self.print_footer()

    def check_new_ras(self, ras):
        for ra in ras:
            if (
                self.recent_ra_types == {}
                or ra["acas_ra"]["advisory"] not in self.recent_ra_types.keys()
            ):
                self.recent_ra_types[ra["acas_ra"]["advisory"]] = ra["acas_ra"][
                    "unix_timestamp"
                ]
                ra_message = (
                    f"""TCAS Resolution Advisory: {ra["acas_ra"]["advisory"]}"""
                )
                if ra["acas_ra"]["advisory_complement"] != "":
                    ra_message += f", {ra['acas_ra']['advisory_complement']}"
                if bool(int(ra["acas_ra"]["MTE"])):
                    ra_message += ", Multi threat"

                if "threat_id_hex" in ra["acas_ra"].keys():
                    threat_reg = get_aircraft_reg_by_icao(
                        ra["acas_ra"]["threat_id_hex"]
                    )
                    threat_id = (
                        threat_reg
                        if threat_reg is not None
                        else f"""ICAO: {ra["acas_ra"]["threat_id_hex"]}"""
                    )
                    ra_message += f", invader: {threat_id}"

                # map_img_filename = os.path.join(
                #     tempfile.gettempdir(),
                #     "plane-notify",
                #     "imgs",
                #     f"{self.active_icao.upper()}_{image_type}_{timestamp}_map",
                # )
                # Map generation for RA is currently disabled, more complex data is needed

                self.notification_manager.set_one_time_exclusive([Providers.DISCORD])
                self.notification_manager.post_to_all(
                    message=ra_message,
                    title=self.title,
                    reg=self.reg,
                    image_path=None,
                )
                # cleanup_images(map_img_filename)

    def expire_ra_types(self):
        if self.recent_ra_types != {}:
            for ra_type, postime in self.recent_ra_types.copy().items():
                timestamp = datetime.fromtimestamp(postime)
                time_since_ra = datetime.now() - timestamp
                logger.debug(time_since_ra)
                if time_since_ra.seconds >= 600:
                    logger.info("Expiring RA: %s", ra_type)
                    self.recent_ra_types.pop(ra_type)
