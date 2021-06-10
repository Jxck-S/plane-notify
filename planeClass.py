from datetime import datetime
class Plane:
    def __init__(self, icao, config_path, config):
        """Initializes a plane object from its config file and given icao."""
        self.icao = icao.upper()
        self.callsign = None
        self.reg = None
        self.config = config
        self.conf_file_path = config_path
        self.alt_ft = None
        self.last_alt_ft = None
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
        self.map_file_name = f"{tempfile.gettempdir()}\\{icao.upper()}_map.png"
        self.last_latitude = None
        self.last_longitude = None
        self.last_contact = None
        self.landing_plausible = False
        self.squawks = [None, None, None, None]
        self.nav_modes = None
        self.last_nav_modes = None
        self.recheck_to = None
        self.speed = None
        self.nearest_airport_dict = None
        self.recent_ra_types = {}
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
            self.__dict__.update({'icao' : ac_dict.icao24.upper(), 'callsign' : ac_dict.callsign, 'latitude' : ac_dict.latitude, 'longitude' : ac_dict.longitude,  'on_ground' : bool(ac_dict.on_ground), 'last_contact' : ac_dict.last_contact})
            if ac_dict.baro_altitude != None:
                self.alt_ft = round(float(ac_dict.baro_altitude)  * 3.281)
            elif self.on_ground:
                self.alt_ft = 0
            #Insert newest sqwauk at 0, sqwuak length should be 4 long 0-3
            self.squawks.insert(0, ac_dict.squawk)
            #Removes oldest sqwauk index 4 5th sqwauk
            if len(self.squawks) == 5:
                self.squawks.pop(4)
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
            self.__dict__.update({'icao' : ac_dict['icao'].upper(), 'callsign' : ac_dict['call'], 'reg' : ac_dict['reg'], 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'alt_ft' : int(ac_dict['alt']), 'on_ground' : bool(int(ac_dict["gnd"])), 'last_contact' : round(float(ac_dict["postime"])/1000)})
            if self.on_ground:
                self.alt_ft = 0
            #Insert newest sqwauk at 0, sqwuak length should be 4 long 0-3
            self.squawks.insert(0, ac_dict.get('sqk'))
            #Removes oldest sqwauk index 4 5th sqwauk
            if len(self.squawks) == 5:
                self.squawks.pop(4)
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
            if 'nav_modes' in ac_dict:
                self.nav_modes = ac_dict['nav_modes']
                for idx, mode in enumerate(self.nav_modes):
                    if mode.upper() in ['TCAS', 'LNAV', 'VNAV']:
                        self.nav_modes[idx] = self.nav_modes[idx].upper()
                    else:
                        self.nav_modes[idx] = self.nav_modes[idx].capitalize()
            #Insert newest sqwauk at 0, sqwuak length should be 4 long 0-3
            self.squawks.insert(0, ac_dict.get('squawk'))
            #Removes oldest sqwauk index 4 5th sqwauk
            if len(self.squawks) == 5:
                self.squawks.pop(4)
            if "nav_altitude_fms" in ac_dict:
                self.nav_altitude = ac_dict['nav_altitude_fms']
            if "nav_altitude_mcp" in ac_dict:
                self.nav_altitude = ac_dict['nav_altitude_mcp']
            else:
                self.nav_altitude = None

            from datetime import datetime, timedelta
            #Create last seen timestamp from how long ago in secs a pos was rec
            now = datetime.now()
            last_pos_datetime = now - timedelta(seconds= ac_dict["seen_pos"])
            self.last_contact = datetime.timestamp(last_pos_datetime)
        except (ValueError, KeyError) as e:

            print("Got data but some data is invalid!")
            print(e)
            print (Fore.YELLOW +"ADSBX Sourced Data: ", ac_dict, Style.RESET_ALL)
            self.printheader("foot")
        else:
            self.feeding = True
            self.run_check()
    def printheader(self, type):
        from colorama import Fore, Back, Style
        if type == "head":
            header = str("--------- " + self.conf_file_path + " ---------------------------- ICAO: " +  self.icao + " ---------------------------------------")
        elif type == "foot":
            header = "----------------------------------------------------------------------------------------------------"
        print(Back.MAGENTA + header[0:100] + Style.RESET_ALL)
    def get_time_since(self, last_contact):
        if last_contact != None:
            last_contact_dt = datetime.fromtimestamp(last_contact)
            time_since_contact = datetime.now() - last_contact_dt
        else:
            time_since_contact = None
        return time_since_contact
    def run_empty(self):
        self.printheader("head")
        self.feeding = False
        self.run_check()
    def run_check(self):
        """Runs a check of a plane module to see if its landed or takenoff using plane data, and takes action if so."""
        #Ability to Remove old Map
        import os
        from colorama import Fore, Style
        from tabulate import tabulate
        from modify_image import append_airport
        from defAirport import getClosestAirport

        #Proprietary Route Lookup
        if os.path.isfile("lookup_route.py"):
            from lookup_route import lookup_route
            ENABLE_ROUTE_LOOKUP = True
        else:
            ENABLE_ROUTE_LOOKUP = False
        if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
            from defMap import getMap
        elif self.config.get('MAP', 'OPTION') == "ADSBX":
            from defSS import get_adsbx_screenshot
            if self.config.has_option('MAP', 'OVERLAYS'):
                self.overlays = self.config.get('MAP', 'OVERLAYS')
            else:
                self.overlays = ""
        else:
            raise ValueError("Map option not set correctly in this planes conf")
        if self.config.getboolean('DISCORD', 'ENABLE'):
            from defDiscord import sendDis
        if self.feeding == False:
            time_since_contact = self.get_time_since(self.last_contact)
            output = [
            [(Fore.CYAN + "ICAO" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.icao + Style.RESET_ALL)],
            [(Fore.CYAN + "Last Contact" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(time_since_contact) + Style.RESET_ALL)] if time_since_contact != None else None
            ]
            output = list(filter(None, output))
            print(tabulate(output, [], 'fancy_grid'))
            print("No Data")
        elif self.feeding == True:
            time_since_contact = self.get_time_since(self.last_contact)
            output = [
            [(Fore.CYAN + "ICAO" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.icao + Style.RESET_ALL)],
            [(Fore.CYAN + "Callsign" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.callsign + Style.RESET_ALL)] if self.callsign != None else None,
            [(Fore.CYAN + "Reg" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.reg + Style.RESET_ALL)] if self.reg != None else None,
            #Squawks are latest to oldest
            [(Fore.CYAN + "Squawks" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + ', '.join("NA" if  x == None else x for x in self.squawks) + Style.RESET_ALL)],
            [(Fore.CYAN + "Coordinates" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.latitude) + ", " + str(self.longitude) + Style.RESET_ALL)],
            [(Fore.CYAN + "Last Contact" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(time_since_contact).split(".")[0]+ Style.RESET_ALL)],
            [(Fore.CYAN + "On Ground" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.on_ground) + Style.RESET_ALL)],
            [(Fore.CYAN + "Baro Altitude" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str("{:,} ft".format(self.alt_ft)) + Style.RESET_ALL)],
            [(Fore.CYAN + "Nav Modes" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + ', '.join(self.nav_modes)  + Style.RESET_ALL)] if "nav_modes" in self.__dict__ and self.nav_modes != None else None,
            [(Fore.CYAN + "Sel Alt Ft" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str("{:,} ft".format(self.nav_altitude)) + Style.RESET_ALL)] if "nav_altitude" in self.__dict__ and self.nav_altitude != None else None
            ]
            output = list(filter(None, output))
            print(tabulate(output, [], 'fancy_grid'))

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
                self.trigger_type = "no longer on ground"
                type_header = "Took off from"
            elif self.last_feeding is False and self.feeding and self.landing_plausible == False:
                nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
                if nearest_airport_dict['elevation_ft'] != "":
                    alt_above_airport = (self.alt_ft - int(nearest_airport_dict['elevation_ft']))
                    print(f"AGL nearest airport: {alt_above_airport}")
                else:
                    alt_above_airport = None
                if (alt_above_airport != None and alt_above_airport <= 10000) or self.alt_ft <= 15000:
                    self.tookoff = True
                    self.trigger_type = "data acquisition"
                    type_header = "Took off near"
            else:
                self.tookoff = False
        else:
            self.tookoff = False

#Check if Landed
        if self.on_ground and self.last_on_ground is False and self.last_below_desired_ft:
            self.landed = True
            self.trigger_type = "now on ground"
            type_header = "Landed in"
            self.landing_plausible = False
        #Set status for landing plausible
        elif self.below_desired_ft and self.last_feeding and self.feeding is False and self.last_on_ground is False:
            self.landing_plausible = True
            print("Near landing conditions, if contiuned data loss for 5 mins, and  if under 10k AGL landing true")

        elif self.landing_plausible and self.feeding is False and time_since_contact.total_seconds() >= 300:
            nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
            if nearest_airport_dict['elevation_ft'] != "":
                alt_above_airport = (self.alt_ft - int(nearest_airport_dict['elevation_ft']))
                print(f"AGL nearest airport: {alt_above_airport}")
            else:
                alt_above_airport = None
            if (alt_above_airport != None and alt_above_airport <= 10000) or self.alt_ft <= 15000:
                self.landing_plausible = False
                self.landed = True
                self.trigger_type = "data loss"
                type_header = "Landed near"
            else:
                print("Alt greater then 10k AGL")
                self.landing_plausible = False
        else:
            self.landed = False

        if self.landed:
            print ("Landed by", self.trigger_type)
        if self.tookoff:
            print("Tookoff by", self.trigger_type)
        #Find nearest airport, and location
        if self.landed or self.tookoff:
            if "nearest_airport_dict" in globals():
                pass #Airport already set
            elif self.trigger_type in ["now on ground", "data acquisition", "data loss"]:
                nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
            elif self.trigger_type == "no longer on ground":
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
                    extra_route_info = lookup_route(self.reg, (self.latitude, self.longitude), self.type, self.alt_ft)
                    if extra_route_info == None:
                        self.recheck_to = True
                        self.nearest_takeoff_airport = nearest_airport_dict
                    else:
                        from defAirport import get_airport_by_icao
                        to_airport = get_airport_by_icao(extra_route_info['apdstic'])
                        code = to_airport['iata_code'] if to_airport['iata_code'] != "" else to_airport['icao']
                        airport_text = f" {code}, {to_airport['name']}"
                        if extra_route_info['apdstic'] != nearest_airport_dict['icao']:
                            route_to = "Going to" + airport_text + " arriving " + extra_route_info['arrivalRelative']
                        else:
                            route_to = f"Will be returning to {airport_text} {extra_route_info['arrivalRelative']}"
            elif self.landed and self.takeoff_time != None:
                landed_time = datetime.utcnow() - self.takeoff_time
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
                getMap((municipality + ", "  + state + ", "  + country_code), self.map_file_name)
            elif self.config.get('MAP', 'OPTION') == "ADSBX":
                url_params = f"icao={self.icao}&zoom=9&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays=" + self.overlays
                get_adsbx_screenshot(self.map_file_name, url_params)
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
                alt_text = f"Reg: {self.reg} On Ground: {str(self.on_ground)} Alt: {str(self.alt_ft)} Last Contact: {str(time_since_contact)} Trigger: {self.trigger_type}"
                self.tweet_api.create_media_metadata(media_id= twitter_media_map_obj.media_id, alt_text= alt_text)
                self.tweet_api.update_status(status = ((self.twitter_title + " " + message).strip()), media_ids=[twitter_media_map_obj.media_id])
            os.remove(self.map_file_name)
        #Recheck Proprietary Route Lookup a minute later if infomation was not available on takeoff.
        if self.recheck_to and self.takeoff_time is not None and (datetime.utcnow() - self.takeoff_time).total_seconds() > 60:
            self.recheck_to = False
            extra_route_info = lookup_route(self.reg, (self.latitude, self.longitude), self.type, self.alt_ft)
            nearest_airport_dict = self.nearest_takeoff_airport
            self.nearest_takeoff_airport = None
            if extra_route_info != None:
                from defAirport import get_airport_by_icao
                to_airport = get_airport_by_icao(extra_route_info['apdstic'])
                code = to_airport['iata_code'] if to_airport['iata_code'] != "" else to_airport['icao']
                airport_text = f" {code}, {to_airport['name']}"
                if extra_route_info['apdstic'] != nearest_airport_dict['icao']:
                    route_to = "Going to" + airport_text + " arriving " + extra_route_info['arrivalRelative']
                else:
                    route_to = f"Will be returning to {airport_text} {extra_route_info['arrivalRelative']}"
                print(route_to)
                #Discord
                if self.config.getboolean('DISCORD', 'ENABLE'):
                    dis_message = f"{self.dis_title} {route_to}".strip()
                    role_id = self.config.get('DISCORD', 'ROLE_ID') if self.config.has_option('DISCORD', 'ROLE_ID') else None
                    sendDis(dis_message, self.config, role_id = role_id)
                #Twitter
                if self.config.getboolean('TWITTER', 'ENABLE'):
                    tweet = self.tweet_api.user_timeline(count = 1)[0]
                    self.tweet_api.update_status(status = f"{self.twitter_title} {route_to}".strip(), in_reply_to_status_id = tweet.id)

        if self.feeding:
            #Squawks
            squawks =[("7500", "Hijacking"), ("7600", "Radio Failure"), ("7700", "Emergency")]
            for squawk in squawks:
                if all(v == squawk[0] for v in (self.squawks[0:2])) and self.squawks[2] != self.squawks[3] and None not in self.squawks:
                    squawk_message = ("Squawking " + squawk[0] + ", " + squawk[1])
                    print(squawk_message)
                    #Google Map or tar1090 screenshot
                    if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
                        getMap((municipality + ", "  + state + ", "  + country_code), self.map_file_name)
                    if self.config.get('MAP', 'OPTION') == "ADSBX":
                        url_params = f"icao={self.icao}&zoom=9&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays=" + self.overlays
                        get_adsbx_screenshot(self.map_file_name, url_params)
                    #Discord
                    if self.config.getboolean('DISCORD', 'ENABLE'):
                        dis_message =  (self.dis_title + " "  + squawk_message)
                        sendDis(dis_message, self.config, self.map_file_name)
                    os.remove(self.map_file_name)
            #Nav Modes Notifications
            if self.nav_modes != None and self.last_nav_modes != None:
                for mode in self.nav_modes:
                    if mode not in self.last_nav_modes:
                        #Discord
                        print(mode, "enabled")
                        if self.config.getboolean('DISCORD', 'ENABLE'):
                            dis_message =  (self.dis_title + " "  + mode + " mode enabled.")
                            if mode == "Approach":
                                url_params = f"icao={self.icao}&zoom=9&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays={self.overlays}"
                                get_adsbx_screenshot(self.map_file_name, url_params)
                                sendDis(dis_message, self.config, self.map_file_name)
                            elif mode in ["Althold", "VNAV", "LNAV"] and self.nav_altitude != None:
                                sendDis((dis_message + ", Sel Alt. " + str(self.nav_altitude) + ", Current Alt. " + str(self.alt_ft)), self.config)
                            else:
                                sendDis(dis_message, self.config)
            # #Power Up
            # if self.last_feeding == False and self.speed == 0 and self.on_ground:
            #     if self.config.getboolean('DISCORD', 'ENABLE'):
            #         dis_message = (self.dis_title + "Powered Up").strip()
            #         sendDis(dis_message, self.config)


#Set Variables to compare to next check
        self.last_feeding = self.feeding
        self.last_alt_ft = self.alt_ft
        self.last_on_ground = self.on_ground
        self.last_below_desired_ft = self.below_desired_ft
        self.last_longitude = self.longitude
        self.last_latitude = self.latitude
        self.last_nav_modes = self.nav_modes


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
                    from defSS import get_adsbx_screenshot, generate_adsbx_screenshot_time_params, generate_adsbx_overlay_param
                    url_params = generate_adsbx_screenshot_time_params(ra['acas_ra']['unix_timestamp']) + f"&lat={ra['lat']}&lon={ra['lon']}&zoom=11&largeMode=2&hideButtons&hideSidebar&mapDim=0&overlays={self.overlays}&timestamp={ra['acas_ra']['unix_timestamp']}"
                    if "threat_id_hex" in ra['acas_ra'].keys():
                        from mictronics_parse import get_aircraft_by_icao
                        threat_reg = get_aircraft_by_icao(ra['acas_ra']['threat_id_hex'])[0]
                        threat_id = threat_reg if threat_reg is not None else "ICAO: " + ra['acas_ra']['threat_id_hex']
                        ra_message += f", invader: {threat_id}"
                        url_params += f"&icao={ra['acas_ra']['threat_id_hex']},{self.icao.lower()}"
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