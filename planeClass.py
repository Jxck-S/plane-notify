from datetime import datetime, timedelta
class Plane:
    import configparser
    main_config = configparser.ConfigParser()
    main_config.read('./configs/mainconf.ini')
    def __init__(self, icao, config_path, config):
        """Initializes a plane object from its config file and given icao."""
        self.icao = icao.upper()
        self.callsign = None
        self.reg = None
        self.config = config
        self.conf_file_path = config_path
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
        import tempfile
        self.map_file_name = f"{tempfile.gettempdir()}/{icao.upper()}_map.png"
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
        if self.config.has_option('DATA', 'DATA_LOSS_MINS'):
            self.data_loss_mins = self.config.getint('DATA', 'DATA_LOSS_MINS')
        else:
            self.data_loss_mins = Plane.main_config.getint('DATA', 'DATA_LOSS_MINS')
        #Setup Tweepy
        if self.config.getboolean('TWITTER', 'ENABLE'):
            from defTweet import tweepysetup
            self.tweet_api = tweepysetup(self.config)
        #Setup PushBullet
        if self.config.getboolean('PUSHBULLET', 'ENABLE'):
            from pushbullet import Pushbullet
            self.pb = Pushbullet(self.config['PUSHBULLET']['API_KEY'])
            self.pb_channel = self.pb.get_channel(self.config.get('PUSHBULLET', 'CHANNEL_TAG'))
    def run_opens(self, ac_dict):
        #Parse OpenSky Vector
        from colorama import Fore, Back, Style
        self.printheader("head")
        #print (Fore.YELLOW + "OpenSky Sourced Data: ", ac_dict)
        try:
            self.__dict__.update({'icao' : ac_dict.icao24.upper(), 'callsign' : ac_dict.callsign, 'latitude' : ac_dict.latitude, 'longitude' : ac_dict.longitude,  'on_ground' : bool(ac_dict.on_ground), 'squawk' : ac_dict.squawk, 'track' : float(ac_dict.heading)})
            if ac_dict.baro_altitude != None:
                self.alt_ft = round(float(ac_dict.baro_altitude)  * 3.281)
            elif self.on_ground:
                self.alt_ft = 0
            from mictronics_parse import get_aircraft_reg_by_icao, get_type_code_by_icao
            self.reg = get_aircraft_reg_by_icao(self.icao)
            self.type = get_type_code_by_icao(self.icao)
            self.last_pos_datetime = datetime.fromtimestamp(ac_dict.time_position)
        except ValueError as e:
            print("Got data but some data is invalid!")
            print(e)
            self.printheader("foot")
        else:
            self.feeding = True
            self.run_check()
    def run_adsbx_v1(self, ac_dict):
        #Parse ADBSX V1 Vector
        from colorama import Fore, Back, Style
        self.printheader("head")
        #print (Fore.YELLOW +"ADSBX Sourced Data: ", ac_dict, Style.RESET_ALL)
        try:
            #postime is divided by 1000 to get seconds from milliseconds, from timestamp expects secs.
            self.__dict__.update({'icao' : ac_dict['icao'].upper(), 'callsign' : ac_dict['call'], 'reg' : ac_dict['reg'], 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'alt_ft' : int(ac_dict['alt']), 'on_ground' : bool(int(ac_dict["gnd"])), 'squawk' : ac_dict['sqk'], 'track' : float(ac_dict["trak"])})
            if self.on_ground:
                self.alt_ft = 0
            self.last_pos_datetime = datetime.fromtimestamp(int(ac_dict['postime'])/1000)
        except ValueError as e:

            print("Got data but some data is invalid!")
            print(e)
            print (Fore.YELLOW +"ADSBX Sourced Data: ", ac_dict, Style.RESET_ALL)
            self.printheader("foot")
        else:
            self.feeding = True
            self.run_check()

    def run_adsbx_v2(self, ac_dict):
        #Parse ADBSX V2 Vector
        from colorama import Fore, Back, Style
        self.printheader("head")
        print(ac_dict)
        try:
            self.__dict__.update({'icao' : ac_dict['hex'].upper(), 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'speed': ac_dict['gs']})
            if "r" in ac_dict:
                self.reg = ac_dict['r']
            if "t" in ac_dict:
                self.type = ac_dict['t']
            if ac_dict['alt_baro'] != "ground":
                self.alt_ft = int(ac_dict['alt_baro'])
                self.on_ground = False
            elif ac_dict['alt_baro'] == "ground":
                self.alt_ft = 0
                self.on_ground = True
            if ac_dict.get('flight') is not None:
                self.callsign = ac_dict.get('flight').strip()
            if ac_dict.get('dbFlags') is not None:
                self.db_flags = ac_dict['dbFlags']
            if 'nav_modes' in ac_dict:
                self.nav_modes = ac_dict['nav_modes']
                for idx, mode in enumerate(self.nav_modes):
                    if mode.upper() in ['TCAS', 'LNAV', 'VNAV']:
                        self.nav_modes[idx] = self.nav_modes[idx].upper()
                    else:
                        self.nav_modes[idx] = self.nav_modes[idx].capitalize()
            self.squawk = ac_dict.get('squawk')
            if "track" in ac_dict:
                self.track = ac_dict['track']
            if "nav_altitude_fms" in ac_dict:
                self.sel_nav_alt = ac_dict['nav_altitude_fms']
            elif "nav_altitude_mcp" in ac_dict:
                self.sel_nav_alt = ac_dict['nav_altitude_mcp']
            else:
                self.sel_nav_alt = None

            #Create last seen timestamp from how long ago in secs a pos was rec
            self.last_pos_datetime = datetime.now() - timedelta(seconds= ac_dict["seen_pos"])
        except (ValueError, KeyError) as e:

            print("Got data but some data is invalid!")
            print(e)
            print (Fore.YELLOW +"ADSBX Sourced Data: ", ac_dict, Style.RESET_ALL)
            self.printheader("foot")
        else:
            #Error Handling for bad data, sometimes it would seem to be ADSB Decode error
            if (not self.on_ground)  and self.speed <= 10:
                print("Not running check, appears to be bad ADSB Decode")
            else:
                self.feeding = True
                self.run_check()
    def __str__(self):
        from colorama import Fore, Back, Style
        from tabulate import tabulate
        if self.last_pos_datetime is not None:
            time_since_contact = self.get_time_since(self.last_pos_datetime)
        output = [
        [(Fore.CYAN + "ICAO" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.icao + Style.RESET_ALL)],
        [(Fore.CYAN + "Callsign" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.callsign + Style.RESET_ALL)] if self.callsign is not None else None,
        [(Fore.CYAN + "Reg" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.reg + Style.RESET_ALL)] if self.reg is not None else None,
        [(Fore.CYAN + "Squawk" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.squawk + Style.RESET_ALL)] if self.squawk is not None else None,
        [(Fore.CYAN + "Coordinates" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.latitude) + ", " + str(self.longitude) + Style.RESET_ALL)] if self.latitude is not None and self.longitude is not None else None,
        [(Fore.CYAN + "Last Contact" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(time_since_contact).split(".")[0]+ Style.RESET_ALL)] if self.last_pos_datetime is not None else None,
        [(Fore.CYAN + "On Ground" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.on_ground) + Style.RESET_ALL)] if self.on_ground is not None else None,
        [(Fore.CYAN + "Baro Altitude" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str("{:,} ft".format(self.alt_ft)) + Style.RESET_ALL)] if self.alt_ft is not None else None,
        [(Fore.CYAN + "Nav Modes" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + ', '.join(self.nav_modes)  + Style.RESET_ALL)] if "nav_modes" in self.__dict__ and self.nav_modes != None else None,
        [(Fore.CYAN + "Sel Alt Ft" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str("{:,} ft".format(self.sel_nav_alt)) + Style.RESET_ALL)] if "sel_nav_alt" in self.__dict__ and self.sel_nav_alt is not None else None
        ]
        output = list(filter(None, output))
        return tabulate(output, [], 'fancy_grid')
    def printheader(self, type):
        from colorama import Fore, Back, Style
        if type == "head":
            header = str("--------- " + self.conf_file_path + " ---------------------------- ICAO: " +  self.icao + " ---------------------------------------")
        elif type == "foot":
            header = "----------------------------------------------------------------------------------------------------"
        print(Back.MAGENTA + header[0:100] + Style.RESET_ALL)
    def get_time_since(self, datetime_obj):
        if datetime_obj != None:
            time_since = datetime.now() - datetime_obj
        else:
            time_since = None
        return time_since
    def get_adsbx_map_overlays(self):
        if self.config.has_option('MAP', 'OVERLAYS'):
            overlays = self.config.get('MAP', 'OVERLAYS')
        else:
            overlays = ""
        return overlays
    def route_info(self):
        from lookup_route import lookup_route, clean_data
        def route_format(extra_route_info, type):
            from defAirport import get_airport_by_icao
            to_airport = get_airport_by_icao(self.known_to_airport)
            code = to_airport['iata_code'] if to_airport['iata_code'] != "" else to_airport['icao']
            airport_text = f"{code}, {to_airport['name']}"
            if 'time_to' in extra_route_info.keys() and type != "divert":
                arrival_rel = "in ~" + extra_route_info['time_to']
            else:
                arrival_rel = None
            if self.known_to_airport != self.nearest_from_airport:
                if type == "inital":
                    header = "Going to"
                elif type == "change":
                    header = "Now going to"
                elif type == "divert":
                    header = "Now diverting to"
                area = f"{to_airport['municipality']}, {to_airport['region']}, {to_airport['iso_country']}"
                route_to = f"{header} {area} ({airport_text})" + (f" arriving {arrival_rel}" if arrival_rel is not None else "")
            else:
                if type == "inital":
                    header = "Will be returning to"
                elif type == "change":
                    header = "Now returning to"
                elif type == "divert":
                    header = "Now diverting back to"
                route_to = f"{header} {airport_text}" + (f" {arrival_rel}" if arrival_rel is not None else "")
            return route_to
        if hasattr(self, "type"):
            extra_route_info = clean_data(lookup_route(self.reg, (self.latitude, self.longitude), self.type, self.alt_ft))
        else:
            extra_route_info = None
        route_to = None
        if extra_route_info is None:
            pass
        elif extra_route_info is not None:
            #Diversion
            if "divert_icao" in extra_route_info.keys():
                if self.known_to_airport != extra_route_info["divert_icao"]:
                    self.known_to_airport = extra_route_info['divert_icao']
                    route_to = route_format(extra_route_info, "divert")
            #Destination
            elif "dest_icao" in extra_route_info.keys():
                #Inital Destination Found
                if self.known_to_airport is None:
                    self.known_to_airport = extra_route_info['dest_icao']
                    route_to = route_format(extra_route_info, "inital")
                #Destination Change
                elif self.known_to_airport != extra_route_info["dest_icao"]:
                    self.known_to_airport = extra_route_info['dest_icao']
                    route_to = route_format(extra_route_info, "change")

        return route_to
    def run_empty(self):
        self.printheader("head")
        self.feeding = False
        self.run_check()
    def run_check(self):
        """Runs a check of a plane module to see if its landed or takenoff using plane data, and takes action if so."""
        print(self)
        #Ability to Remove old Map
        import os
        from colorama import Fore, Style
        from tabulate import tabulate
        #Proprietary Route Lookup
        if os.path.isfile("lookup_route.py") and (self.db_flags is None or not self.db_flags & 1):
            from lookup_route import lookup_route
            ENABLE_ROUTE_LOOKUP = True
        else:
            ENABLE_ROUTE_LOOKUP = False
        if self.config.getboolean('DISCORD', 'ENABLE'):
            from defDiscord import sendDis
        if self.last_pos_datetime is not None:
            time_since_contact = self.get_time_since(self.last_pos_datetime)
#Check if below desire ft
        desired_ft = 15000
        if self.alt_ft is None or self.alt_ft > desired_ft:
            self.below_desired_ft = False
        elif self.alt_ft < desired_ft:
            self.below_desired_ft = True
#Check if tookoff
        if self.below_desired_ft and self.on_ground is False:
            if self.last_on_ground:
                self.tookoff = True
                trigger_type = "no longer on ground"
                type_header = "Took off from"
            elif self.last_feeding is False and self.feeding and self.landing_plausible == False:
                from defAirport import getClosestAirport
                nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
                if nearest_airport_dict['elevation_ft'] != "":
                    alt_above_airport = (self.alt_ft - int(nearest_airport_dict['elevation_ft']))
                    print(f"AGL nearest airport: {alt_above_airport}")
                else:
                    alt_above_airport = None
                if (alt_above_airport != None and alt_above_airport <= 10000) or self.alt_ft <= 15000:
                    self.tookoff = True
                    trigger_type = "data acquisition"
                    type_header = "Took off near"
            else:
                self.tookoff = False
        else:
            self.tookoff = False

#Check if Landed
        if self.on_ground and self.last_on_ground is False and self.last_below_desired_ft:
            self.landed = True
            trigger_type = "now on ground"
            type_header = "Landed in"
            self.landing_plausible = False
        #Set status for landing plausible
        elif self.below_desired_ft and self.last_feeding and self.feeding is False and self.last_on_ground is False:
            self.landing_plausible = True
            print("Near landing conditions, if contiuned data loss for configured time, and  if under 10k AGL landing true")

        elif self.landing_plausible and self.feeding is False and time_since_contact.total_seconds() >= (self.data_loss_mins * 60):
            from defAirport import getClosestAirport
            nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
            if nearest_airport_dict['elevation_ft'] != "":
                alt_above_airport = (self.alt_ft - int(nearest_airport_dict['elevation_ft']))
                print(f"AGL nearest airport: {alt_above_airport}")
            else:
                alt_above_airport = None
            if (alt_above_airport != None and alt_above_airport <= 10000) or self.alt_ft <= 15000:
                self.landing_plausible = False
                self.on_ground = None
                self.landed = True
                trigger_type = "data loss"
                type_header = "Landed near"
            else:
                print("Alt greater then 10k AGL")
                self.landing_plausible = False
                self.on_ground = None
        else:
            self.landed = False

        if self.landed:
            print ("Landed by", trigger_type)
        if self.tookoff:
            print("Tookoff by", trigger_type)
        #Find nearest airport, and location
        if self.landed or self.tookoff:
            from defAirport import getClosestAirport
            if "nearest_airport_dict" in globals():
                pass #Airport already set
            elif trigger_type in ["now on ground", "data acquisition", "data loss"]:
                nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
            elif trigger_type == "no longer on ground":
                nearest_airport_dict = getClosestAirport(self.last_latitude, self.last_longitude, self.config.get("AIRPORT", "TYPES"))
            #Convert dictionary keys to sep variables
            country_code = nearest_airport_dict['iso_country']
            state = nearest_airport_dict['region'].strip()
            municipality = nearest_airport_dict['municipality'].strip()
            if municipality == "" or state == "" or municipality == state:
                if municipality != "":
                    area = municipality
                elif state != "":
                    area = state
                else:
                    area = ""
            else:
                area = f"{municipality}, {state}"
            location_string = (f"{area}, {country_code}")
            print (Fore.GREEN + "Country Code:", country_code, "State:", state, "Municipality:", municipality + Style.RESET_ALL)
        title_switch = {
        "reg": self.reg,
        "callsign": self.callsign,
        "icao": self.icao,
        }
    #Set Discord Title
        if self.config.getboolean('DISCORD', 'ENABLE'):
            self.dis_title = (title_switch.get(self.config.get('DISCORD', 'TITLE')) or "NA").strip() if self.config.get('DISCORD', 'TITLE') in title_switch.keys() else self.config.get('DISCORD', 'TITLE')
    #Set Twitter Title
        if self.config.getboolean('TWITTER', 'ENABLE'):
            self.twitter_title = (title_switch.get(self.config.get('TWITTER', 'TITLE')) or "NA") if self.config.get('TWITTER', 'TITLE') in title_switch.keys() else self.config.get('TWITTER', 'TITLE')
    #Takeoff and Land Notification
        if self.tookoff or self.landed:
            route_to = None
            if self.tookoff:
                self.takeoff_time = datetime.utcnow()
                landed_time_msg = None
                #Proprietary Route Lookup
                if ENABLE_ROUTE_LOOKUP:
                    self.nearest_from_airport = nearest_airport_dict['icao']
                    route_to = self.route_info()
                    if route_to is None:
                        self.recheck_route_time = 1
                    else:
                        self.recheck_route_time = 10
            elif self.landed and self.takeoff_time != None:
                landed_time = datetime.utcnow() - self.takeoff_time
                if trigger_type == "data loss":
                    landed_time -= timedelta(seconds=time_since_contact.total_seconds())
                hours, remainder = divmod(landed_time.total_seconds(), 3600)
                minutes, seconds = divmod(remainder, 60)
                min_syntax = "Mins" if minutes > 1 else "Min"
                if hours > 0:
                    hour_syntax = "Hours" if hours > 1 else "Hour"
                    landed_time_msg = (f"Apx. flt. time {int(hours)} {hour_syntax}" +  (f" : {int(minutes)} {min_syntax}. " if minutes > 0 else "."))
                else:
                    landed_time_msg = (f"Apx. flt. time {int(minutes)} {min_syntax}.")
                self.takeoff_time = None
            elif self.landed:
                landed_time_msg = None
            message = (f"{type_header} {location_string}.") + ("" if route_to is None else f" {route_to}.") + ((f" {landed_time_msg}") if landed_time_msg != None else "")
            print (message)
            #Google Map or tar1090 screenshot
            if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
                from defMap import getMap
                getMap((municipality + ", "  + state + ", "  + country_code), self.map_file_name)
            elif self.config.get('MAP', 'OPTION') == "ADSBX":
                from defSS import get_adsbx_screenshot

                url_params = f"icao={self.icao}&zoom=9&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays=" + self.get_adsbx_map_overlays()
                get_adsbx_screenshot(self.map_file_name, url_params)
                from modify_image import append_airport
                append_airport(self.map_file_name, nearest_airport_dict)
            else:
                raise ValueError("Map option not set correctly in this planes conf")
            #Discord
            if self.config.getboolean('DISCORD', 'ENABLE'):
                dis_message = f"{self.dis_title} {message}".strip()
                role_id = self.config.get('DISCORD', 'ROLE_ID') if self.config.has_option('DISCORD', 'ROLE_ID') else None
                sendDis(dis_message, self.config, self.map_file_name, role_id = role_id)
            #PushBullet
            if self.config.getboolean('PUSHBULLET', 'ENABLE'):
                with open(self.map_file_name, "rb") as pic:
                    map_data = self.pb.upload_file(pic, "Tookoff IMG" if self.tookoff else "Landed IMG")
                self.pb_channel.push_note(self.config.get('PUSHBULLET', 'TITLE'), message)
                self.pb_channel.push_file(**map_data)
            #Twitter
            if self.config.getboolean('TWITTER', 'ENABLE'):
                twitter_media_map_obj = self.tweet_api.media_upload(self.map_file_name)
                alt_text = f"Reg: {self.reg} On Ground: {str(self.on_ground)} Alt: {str(self.alt_ft)} Last Contact: {str(time_since_contact)} Trigger: {trigger_type}"
                self.tweet_api.create_media_metadata(media_id= twitter_media_map_obj.media_id, alt_text= alt_text)
                self.latest_tweet_id = self.tweet_api.update_status(status = ((self.twitter_title + " " + message).strip()), media_ids=[twitter_media_map_obj.media_id]).id
            os.remove(self.map_file_name)
            if self.landed:
                self.latest_tweet_id = None
                self.recheck_route_time = None
                self.known_to_airport = None
                self.nearest_from_airport = None
        #Recheck Proprietary Route Info.
        if self.takeoff_time is not None and self.recheck_route_time is not None and (datetime.utcnow() - self.takeoff_time).total_seconds() > 60 * self.recheck_route_time:
            self.recheck_route_time += 10
            route_to = self.route_info()
            if route_to != None:
                print(route_to)
                #Discord
                if self.config.getboolean('DISCORD', 'ENABLE'):
                    dis_message = f"{self.dis_title} {route_to}".strip()
                    role_id = self.config.get('DISCORD', 'ROLE_ID') if self.config.has_option('DISCORD', 'ROLE_ID') else None
                    sendDis(dis_message, self.config, role_id = role_id)
                #Twitter
                if self.config.getboolean('TWITTER', 'ENABLE'):
                    #tweet = self.tweet_api.user_timeline(count = 1)[0]
                    self.latest_tweet_id = self.tweet_api.update_status(status = f"{self.twitter_title} {route_to}".strip(), in_reply_to_status_id = self.latest_tweet_id).id

        if self.circle_history is not None:
            #Expires traces for circles
            if self.circle_history["traces"] != []:
                for trace in self.circle_history["traces"]:
                    if (datetime.now() - datetime.fromtimestamp(trace[0])).total_seconds() >= 20*60:
                        print("Trace Expire, removed")
                        self.circle_history["traces"].remove(trace)
            #Expire touchngo
            if "touchngo" in self.circle_history.keys() and (datetime.now() - datetime.fromtimestamp(self.circle_history['touchngo'])).total_seconds() >= 10*60:
                self.circle_history.pop("touchngo")
        if self.feeding:
            #Squawks
            emergency_squawks ={"7500" : "Hijacking", "7600" :"Radio Failure", "7700" : "General Emergency"}
            seen = datetime.now() - self.last_pos_datetime
            #Only run check if emergency data previously set
            if self.last_emergency is not None and not self.emergency_already_triggered:
                time_since_org_emer = datetime.now() - self.last_emergency[0]
                #Checks times to see x time and still same squawk
                if time_since_org_emer.total_seconds() >= 60 and self.last_emergency[1] == self.squawk and seen.total_seconds() <= 60:
                    self.emergency_already_triggered = True
                    squawk_message = (f"{self.dis_title} Squawking {self.last_emergency[1]} {emergency_squawks[self.squawk]}").strip()
                    print(squawk_message)
                    #Google Map or tar1090 screenshot
                    if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
                        getMap((municipality + ", "  + state + ", "  + country_code), self.map_file_name)
                    if self.config.get('MAP', 'OPTION') == "ADSBX":
                        from defSS import get_adsbx_screenshot
                        url_params = f"icao={self.icao}&zoom=9&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays=" + self.get_adsbx_map_overlays()
                        get_adsbx_screenshot(self.map_file_name, url_params)
                    if self.config.getboolean('DISCORD', 'ENABLE'):
                        dis_message =  (self.dis_title + " "  + squawk_message)
                        sendDis(dis_message, self.config, self.map_file_name)
                    os.remove(self.map_file_name)
            #Realizes first time seeing emergency, stores time and type
            elif self.squawk in emergency_squawks.keys() and not self.emergency_already_triggered and not self.on_ground:
                print("Emergency", self.squawk, "detected storing code and time and waiting to trigger")
                self.last_emergency = (self.last_pos_datetime, self.squawk)
            elif self.squawk not in emergency_squawks.keys() and self.emergency_already_triggered:
                self.emergency_already_triggered = None

            #Nav Modes Notifications
            if self.nav_modes != None and self.last_nav_modes != None:
                for mode in self.nav_modes:
                    if mode not in self.last_nav_modes:
                        #Discord
                        print(mode, "enabled")
                        if self.config.getboolean('DISCORD', 'ENABLE'):
                            dis_message =  (self.dis_title + " "  + mode + " mode enabled.")
                            if mode == "Approach":
                                from defSS import get_adsbx_screenshot
                                url_params = f"icao={self.icao}&zoom=9&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays={self.get_adsbx_map_overlays()}"
                                get_adsbx_screenshot(self.map_file_name, url_params)
                                sendDis(dis_message, self.config, self.map_file_name)
                            #elif mode in ["Althold", "VNAV", "LNAV"] and self.sel_nav_alt != None:
                            #    sendDis((dis_message + ", Sel Alt. " + str(self.sel_nav_alt) + ", Current Alt. " + str(self.alt_ft)), self.config)
                            else:
                                sendDis(dis_message, self.config)
            #Selected Altitude
            if self.sel_nav_alt is not None and self.last_sel_alt is not None and self.last_sel_alt != self.sel_nav_alt:
                #Discord
                print("Nav altitude is now", self.sel_nav_alt)
                if self.config.getboolean('DISCORD', 'ENABLE'):
                    dis_message =  (self.dis_title + " Sel.  alt. " + str("{:,} ft".format(self.sel_nav_alt)))
                    sendDis(dis_message,self.config)
            #Circling
            if self.last_track is not None:
                import time
                if self.circle_history is None:
                    self.circle_history = {"traces" : [], "triggered" : False}
                #Add touchngo
                if self.on_ground or self.alt_ft <= 500:
                    self.circle_history["touchngo"] = time.time()
                #Add a Trace
                if self.on_ground is False:
                    from calculate_headings import calculate_deg_change
                    track_change = calculate_deg_change(self.track, self.last_track)
                    track_change = round(track_change, 3)
                    self.circle_history["traces"].append((time.time(), self.latitude, self.longitude, track_change))

                total_change = 0
                coords = []
                for trace in self.circle_history["traces"]:
                    total_change += float(trace[3])
                    coords.append((float(trace[1]), float(trace[2])))

                print("Total Bearing Change", round(total_change, 3))
                #Check Centroid when Bearing change meets req
                if abs(total_change) >= 720 and self.circle_history['triggered'] is False:
                    print("Circling Bearing Change Met")
                    from shapely.geometry import MultiPoint
                    from geopy.distance import geodesic
                    aircraft_coords = (self.latitude, self.longitude)
                    points = MultiPoint(coords)
                    cent =  (points.centroid) #True centroid, not necessarily an existing point
                    #rp =  (points.representative_point()) #A represenative point, not centroid,
                    print(cent)
                    #print(rp)
                    distance_to_centroid = geodesic(aircraft_coords, cent.coords).mi
                    print(f"Distance to centroid of circling coordinates {distance_to_centroid} miles")
                    if distance_to_centroid <= 15:
                        print("Within 15 miles of centroid, CIRCLING")
                        from defAirport import getClosestAirport
                        nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, ["small_airport", "medium_airport", "large_airport"])
                        from calculate_headings import calculate_from_bearing, calculate_cardinal
                        from_bearing = calculate_from_bearing((float(nearest_airport_dict['latitude_deg']), float(nearest_airport_dict['longitude_deg'])), (self.latitude, self.longitude))
                        cardinal = calculate_cardinal(from_bearing)
                        from defSS import get_adsbx_screenshot
                        url_params = f"icao={self.icao}&zoom=10&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays={self.get_adsbx_map_overlays()}"
                        get_adsbx_screenshot(self.map_file_name, url_params)
                        if nearest_airport_dict['distance_mi'] < 3:
                            if "touchngo" in self.circle_history.keys():
                                message = f"Doing touch and goes at {nearest_airport_dict['icao']}"
                            else:
                                message =  f"Circling over {nearest_airport_dict['icao']} at {self.alt_ft}ft"
                        else:
                            message =  f"Circling {round(nearest_airport_dict['distance_mi'], 2)}mi {cardinal} of {nearest_airport_dict['icao']}, {nearest_airport_dict['name']}  at {self.alt_ft}ft"
                        print(message)
                        if self.config.getboolean('DISCORD', 'ENABLE'):
                            role_id = self.config.get('DISCORD', 'ROLE_ID') if self.config.has_option('DISCORD', 'ROLE_ID') else None
                            sendDis(message, self.config, self.map_file_name, role_id)
                        if self.config.getboolean('TWITTER', 'ENABLE'):
                            twitter_media_map_obj = self.tweet_api.media_upload(self.map_file_name)
                            alt_text = f"Distance to centroid: {distance_to_centroid}, Total change: {total_change}"
                            self.tweet_api.create_media_metadata(media_id= twitter_media_map_obj.media_id, alt_text= alt_text)
                            tweet = self.tweet_api.user_timeline(count = 1)[0]
                            self.latest_tweet_id = self.tweet_api.update_status(status = f"{self.twitter_title} {message}".strip(), in_reply_to_status_id = self.latest_tweet_id, media_ids=[twitter_media_map_obj.media_id]).id

                        self.circle_history['triggered'] = True
                elif abs(total_change) <= 360 and self.circle_history["triggered"]:
                    print("No Longer Circling, trigger cleared")
                    self.circle_history['triggered'] = False
            # #Power Up
            # if self.last_feeding == False and self.speed == 0 and self.on_ground:
            #     if self.config.getboolean('DISCORD', 'ENABLE'):
            #         dis_message = (self.dis_title + "Powered Up").strip()
            #         sendDis(dis_message, self.config)


#Set Variables to compare to next check
        self.last_track = self.track
        self.last_feeding = self.feeding
        self.last_on_ground = self.on_ground
        self.last_below_desired_ft = self.below_desired_ft
        self.last_longitude = self.longitude
        self.last_latitude = self.latitude
        self.last_nav_modes = self.nav_modes
        self.last_sel_alt = self.sel_nav_alt


        if self.takeoff_time != None:
            elapsed_time = datetime.utcnow() - self.takeoff_time
            hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            print((f"Time Since Take off  {int(hours)} Hours : {int(minutes)} Mins : {int(seconds)} Secs"))
        self.printheader("foot")
    def check_new_ras(self, ras):
            for ra in ras:
                if self.recent_ra_types == {} or ra['acas_ra']['advisory'] not in self.recent_ra_types.keys():
                    self.recent_ra_types[ra['acas_ra']['advisory']] = ra['acas_ra']['unix_timestamp']
                    ra_message = f"TCAS Resolution Advisory: {ra['acas_ra']['advisory']}"
                    if ra['acas_ra']['advisory_complement'] != "":
                        ra_message += f", {ra['acas_ra']['advisory_complement']}"
                    if bool(int(ra['acas_ra']['MTE'])):
                        ra_message += ", Multi threat"
                    from defSS import get_adsbx_screenshot, generate_adsbx_screenshot_time_params
                    url_params = f"&lat={ra['lat']}&lon={ra['lon']}&zoom=11&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays={self.get_adsbx_map_overlays()}"
                    if "threat_id_hex" in ra['acas_ra'].keys():
                        from mictronics_parse import get_aircraft_reg_by_icao
                        threat_reg = get_aircraft_reg_by_icao(ra['acas_ra']['threat_id_hex'])
                        threat_id = threat_reg if threat_reg is not None else "ICAO: " + ra['acas_ra']['threat_id_hex']
                        ra_message += f", invader: {threat_id}"
                        url_params += generate_adsbx_screenshot_time_params(ra['acas_ra']['unix_timestamp']) + f"&icao={ra['acas_ra']['threat_id_hex']},{self.icao.lower()}&timestamp={ra['acas_ra']['unix_timestamp']}"
                    else:
                        url_params += f"&icao={self.icao.lower()}&noIsolation"
                    print(url_params)
                    get_adsbx_screenshot(self.map_file_name, url_params, True, True)

                    if self.config.getboolean('DISCORD', 'ENABLE'):
                        from defDiscord import sendDis
                        dis_message = f"{self.dis_title} {ra_message}"
                        role_id = self.config.get('DISCORD', 'ROLE_ID') if self.config.has_option('DISCORD', 'ROLE_ID') else None
                        sendDis(dis_message, self.config, self.map_file_name, role_id = role_id)
                    #if twitter
    def expire_ra_types(self):
        if self.recent_ra_types != {}:
            for ra_type, postime in self.recent_ra_types.copy().items():
                timestamp = datetime.fromtimestamp(postime)
                time_since_ra = datetime.now() - timestamp
                print(time_since_ra)
                if time_since_ra.seconds >= 600:
                    print(ra_type)
                    self.recent_ra_types.pop(ra_type)