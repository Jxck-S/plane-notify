class Plane:
    def __init__(self, icao, config_path, config):
        """Initializes a plane object from its config file and given icao."""
        self.icao = icao.upper()
        self.config = config
        self.conf_file_path = config_path
        self.geo_alt_ft = None
        self.last_geo_alt_ft = None
        self.below_desired_ft = None
        self.last_below_desired_ft = None
        self.feeding = None
        self.last_feeding = None
        self.last_on_ground = None
        self.on_ground = None
        self.longitude = None
        self.latitude = None
        self.callsign = None
        self.takeoff_time = None
        self.map_file_name = icao.upper() + "_map.png"
        self.last_latitude = None
        self.last_longitude = None
        self.last_contact = None
        self.landing_plausible = False
    def getICAO(self):
        return self.icao
    def run_OPENS(self, ac_dict):
        #Parse OpenSky Vector
        from colorama import Fore, Back, Style
        self.printheader("head")
        #print (Fore.YELLOW + "OpenSky Sourced Data: ", ac_dict)
        try:
            self.__dict__.update({'icao' : ac_dict.icao24.upper(), 'callsign' : ac_dict.callsign, 'latitude' : ac_dict.latitude, 'longitude' : ac_dict.longitude,  'on_ground' : bool(ac_dict.on_ground), 'last_contact' : ac_dict.last_contact})
            if ac_dict.geo_altitude != None:
                self.geo_alt_ft = round(float(ac_dict.geo_altitude)  * 3.281)
            elif self.on_ground:
                self.geo_alt_ft = 0
        except ValueError as e:
            print("Got data but some data is invalid!")
            print(e)
            self.printheader("foot")
        else:
            self.feeding = True
            self.run_check()
    def run_ADSBX(self, ac_dict):
        #Parse ADBSX Vector
        from colorama import Fore, Back, Style
        self.printheader("head")
        #print (Fore.YELLOW +"ADSBX Sourced Data: ", ac_dict, Style.RESET_ALL)
        try:
            #postime is divided by 1000 to get seconds from milliseconds, from timestamp expects secs.
            self.__dict__.update({'icao' : ac_dict['icao'], 'callsign' : ac_dict['call'], 'reg' : ac_dict['reg'], 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'geo_alt_ft' : int(ac_dict['galt']), 'on_ground' : bool(int(ac_dict["gnd"])), 'last_contact' : round(float(ac_dict["postime"])/1000)})
            if self.on_ground:
                self.geo_alt_ft = 0
            if "to" in ac_dict.keys():
                self.to_location = ac_dict["to"]
            if "from" in ac_dict.keys():
                self.from_location = ac_dict["from"]
        except ValueError as e:

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
        from datetime import datetime
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
        #Import Modules
        #Clear Terminal
        #print("\033[H\033[J")
        #Ability to Remove old Map
        import os
        #Setup Geopy
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="NotifyBot", timeout=5)
        import time
        from colorama import Fore, Back, Style
        #Platform for determining OS for strftime
        import platform
        from datetime import datetime
        from tabulate import tabulate
        from AppendAirport import append_airport
        from defAirport import getClosestAirport
        if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
            from defMap import getMap
        elif self.config.get('MAP', 'OPTION') == "ADSBX":
            from defSS import getSS
            if self.config.has_option('MAP', 'OVERLAYS'):
                self.overlays = self.config.get('MAP', 'OVERLAYS')
            else:
                self.overlays = ""
        else:
            raise Exception("Map option not set correctly in this planes conf")
        if self.config.getboolean('DISCORD', 'ENABLE'):
            from defDiscord import sendDis
        #Setup Tweepy
        if self.config.getboolean('TWITTER', 'ENABLE'):
            from defTweet import tweepysetup
            self.tweet_api = tweepysetup(self.config)
        #Setup PushBullet
        if self.config.getboolean('PUSHBULLET', 'ENABLE'):
            from pushbullet import Pushbullet
            self.pb = Pushbullet(self.config['PUSHBULLET']['API_KEY'])
            self.pb_channel = self.pb.get_channel(self.config.get('PUSHBULLET', 'CHANNEL_TAG'))

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
            [(Fore.CYAN + "Callsign" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.callsign + Style.RESET_ALL)],
            [(Fore.CYAN + "Reg" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.reg + Style.RESET_ALL)] if "reg" in self.__dict__ else None,
            [(Fore.CYAN + "From" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.from_location + Style.RESET_ALL)] if "from_location" in self.__dict__ else None,
            [(Fore.CYAN + "To" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + self.to_location + Style.RESET_ALL)] if "to_location" in self.__dict__ else None,
            [(Fore.CYAN + "Latitude" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.latitude) + Style.RESET_ALL)],
            [(Fore.CYAN + "Longitude" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.longitude) + Style.RESET_ALL)],
            [(Fore.CYAN + "Last Contact" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(time_since_contact).split(".")[0]+ Style.RESET_ALL)],
            [(Fore.CYAN + "On Ground" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str(self.on_ground) + Style.RESET_ALL)],
            [(Fore.CYAN + "GEO Alitude" + Style.RESET_ALL), (Fore.LIGHTGREEN_EX + str("{:,} ft".format(self.geo_alt_ft)) + Style.RESET_ALL)]
            ]
            output = list(filter(None, output))
            print(tabulate(output, [], 'fancy_grid'))

#Check if below desire ft
        desired_ft = 10000
        if self.geo_alt_ft is None or self.geo_alt_ft > desired_ft:
            self.below_desired_ft = False
        elif self.geo_alt_ft < desired_ft:
            self.below_desired_ft = True
#Check if tookoff
        if self.below_desired_ft and self.on_ground is False:
            if self.last_on_ground:
                self.tookoff = True
                self.trigger_type = "no longer on ground"
                self.tookoff_header = "Took off from "
            elif self.last_feeding is False and self.feeding and self.landing_plausible == False:
                self.tookoff = True
                self.trigger_type = "data acquisition"
                self.tookoff_header = "Took off near "
            else:
                self.tookoff = False
        else:
            self.tookoff = False

        #self.tookoff = bool(self.below_desired_ft and self.on_ground is False and ((self.last_feeding is False and self.feeding) or (self.last_on_ground)))
        #print ("Tookoff Just Now:", self.tookoff)


#Check if Landed
        if self.on_ground and self.last_on_ground is False and self.last_below_desired_ft:
            self.landed = True
            self.trigger_type = "now on ground"
            self.landed_header = "Landed in "
            self.landing_plausible = False
        #Set status for landing plausible
        elif self.last_below_desired_ft and self.last_feeding and self.feeding is False and self.last_on_ground is False:
            print("Near landing conditions, if contiuned data loss for 5 mins, landing true")
            self.landing_plausible = True

        elif self.landing_plausible and self.feeding is False and time_since_contact.seconds >= 300:
            self.landing_plausible = False
            self.landed = True
            self.trigger_type = "data loss"
            self.landed_header = "Landed near "
        else:
            self.landed = False

        #self.landed = bool(self.last_below_desired_ft  and ((self.last_feeding and self.feeding is False and self.last_on_ground is False)  or (self.on_ground and self.last_on_ground is False)))
        #print ("Landed Just Now:", self.landed)
        if self.landed:
            print ("Landed by", self.trigger_type)
        if self.tookoff:
            print("Tookoff by", self.trigger_type)
#Lookup Location of coordinates
        if self.landed or self.tookoff:
            if self.trigger_type == "now on ground" or "data acquisition" and self.longitude != None and self.latitude != None:
                combined =  f"{self.latitude} , {self.longitude}"
                nearest_airport_dict = getClosestAirport(self.latitude, self.longitude, self.config.get("AIRPORT", "TYPES"))
                has_coords = True
            elif self.trigger_type == "data loss" or "no longer on ground" and self.last_longitude != None and self.last_latitude != None:
                combined = f"{self.last_latitude}, {self.last_longitude}"
                nearest_airport_dict = getClosestAirport(self.last_latitude, self.last_longitude, self.config.get("AIRPORT", "TYPES"))
                has_coords = True
            else:
                print (Fore.RED + 'No Location, No coordinates')
                invalid_Location = True
                print(Style.RESET_ALL)
            if has_coords:
                try:
                    location = geolocator.reverse(combined)
                except BaseException:
                    print ("Geopy API Error")
                else:
        #           print (Fore.YELLOW, "Geopy debug: ", location.raw, Style.RESET_ALL)
                    #Checking for invalid location, where GeoPy doesn't find coordinates info
                    try:
                        geoError = location.raw['error']
                    except KeyError:
                        invalid_Location = False
                        #Convert Full address to sep variables only if Valid Location
                        address = location.raw['address']
                        country = address.get('country', '')
                        country_code = address.get('country_code', '').upper()
                        state = address.get('state', '')
                        county = address.get('county', '')
                        city = address.get('city', '')
                        town = address.get('town', '')
                        hamlet = address.get('hamlet', '')
            #           print (Fore.YELLOW)
            #           print ("Address Fields debug: ", self.address)
            #           print(Style.RESET_ALL)
                        print (Fore.GREEN)
                        print("Entire Address: ", location.address)
                        print ("Country Code: ", country_code)
                        print ("Country: ", country)
                        print ("State: ", state)
                        print ("City: ", city)
                        print ("Town: ", town)
                        print ("Hamlet: ", hamlet)
                        print ("County: ", county)
                        print(Style.RESET_ALL)
                        #Chose city town county or hamlet for location as not all are always avalible.
                        aera_hierarchy = city or town or county or hamlet
                    else:
                        invalid_Location = True
                        print (Fore.RED)
                        print (geoError)
                        print ("Invalid Location, Likely Over Water ")
                        print(Style.RESET_ALL)

    #Set Discord Title
        if self.config.getboolean('DISCORD', 'ENABLE'):
            self.dis_title = self.icao if self.config.get('DISCORD', 'TITLE') == "icao" else self.callsign if self.config.get('DISCORD', 'TITLE') == "callsign" else self.config.get('DISCORD', 'TITLE')
    #Set Twitter Title
        if self.config.getboolean('TWITTER', 'ENABLE'):
            self.twitter_title = self.icao if self.config.get('TWITTER', 'TITLE') == "icao" else self.callsign if self.config.get('TWITTER', 'TITLE') == "callsign" else self.config.get('TWITTER', 'TITLE')
    #Takeoff Notifcation and Landed
        if self.tookoff:
            if invalid_Location is False:
                tookoff_message = (self.tookoff_header  + aera_hierarchy + ", " + state + ", " + country_code + ". ")
            else:
                tookoff_message = ("Took off")
            print (tookoff_message)
            #Google Map or tar1090 screenshot
            if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
                getMap((aera_hierarchy + ", "  + state + ", "  + country_code), self.icao)
            elif self.config.get('MAP', 'OPTION') == "ADSBX":
                getSS(self.icao, self.overlays)
                if nearest_airport_dict != None:
                    append_airport(self.map_file_name, nearest_airport_dict['icao'], nearest_airport_dict['name'], nearest_airport_dict['distance'])
                    airport_string = nearest_airport_dict['icao'] + ", " + nearest_airport_dict["name"]
                else:
                    airport_string = ""
            else:
                raise Exception("Map option not set correctly in this planes conf")
            #Discord
            if self.config.getboolean('DISCORD', 'ENABLE'):
                dis_message = (self.dis_title + " "  + tookoff_message + airport_string).strip()
                sendDis(dis_message, self.map_file_name, self.config)
            #PushBullet
            if self.config.getboolean('PUSHBULLET', 'ENABLE'):
                with open(self.map_file_name, "rb") as pic:
                    map_data = self.pb.upload_file(pic, "Tookoff IMG")
                self.pb_channel.push_note(self.config.get('PUSHBULLET', 'TITLE'), tookoff_message)
                self.pb_channel.push_file(**map_data)
            #Twitter
            if self.config.getboolean('TWITTER', 'ENABLE'):
                twitter_media_map_obj = self.tweet_api.media_upload(self.map_file_name)
                alt_text = "Call: " + self.callsign + " On Ground: " + str(self.on_ground) + " Alt: " + str(self.geo_alt_ft) + " Last Contact: " + str(time_since_contact) + " Trigger: " + self.trigger_type
                self.tweet_api.create_media_metadata(media_id= twitter_media_map_obj.media_id, alt_text= alt_text)
                self.tweet_api.update_status(status = ((self.twitter_title + " " + tookoff_message).strip()), media_ids=[twitter_media_map_obj.media_id])
                #self.tweet_api.update_with_media(self.map_file_name, status = (self.twitter_title + " " + tookoff_message).strip())
            self.takeoff_time = time.time()
            os.remove(self.map_file_name)


        if self.landed:
            self.landed_time_msg = ""
            if self.takeoff_time != None:
                self.landed_time = time.time() - self.takeoff_time
                if platform.system() == "Linux":
                    self.landed_time_msg = time.strftime("Apx. flt. time %-H Hours : %-M Mins. ", time.gmtime(self.landed_time))
                elif platform.system() == "Windows":
                    self.landed_time_msg = time.strftime("Apx. flt. time %#H Hours : %#M Mins. ", time.gmtime(self.landed_time))
            if invalid_Location is False:
                landed_message = (self.landed_header + aera_hierarchy + ", " + state + ", " + country_code + ". " + self.landed_time_msg)
            else:
                landed_message = ("Landed" + ", " + self.landed_time_msg)
            print (landed_message)
            #Google Map or tar1090 screenshot
            if self.config.get('MAP', 'OPTION') == "GOOGLESTATICMAP":
                getMap((aera_hierarchy + ", "  + state + ", "  + country_code), self.icao)
            elif self.config.get('MAP', 'OPTION') == "ADSBX":
                getSS(self.icao, self.overlays)
                if nearest_airport_dict != None:
                    append_airport(self.map_file_name, nearest_airport_dict['icao'], nearest_airport_dict['name'], nearest_airport_dict['distance'])
                    airport_string = nearest_airport_dict['icao'] + ", " + nearest_airport_dict["name"]
                else:
                    airport_string = ""

            else:
                raise Exception("Map option not set correctly in this planes conf")
            #Discord
            if self.config.getboolean('DISCORD', 'ENABLE'):
                dis_message =  (self.dis_title + " "  + landed_message + " " + airport_string).strip()
                sendDis(dis_message, self.map_file_name, self.config)
            #PushBullet
            if self.config.getboolean('PUSHBULLET', 'ENABLE'):
                with open(self.map_file_name, "rb") as pic:
                    map_data = self.pb.upload_file(pic, "Landed IMG")
                self.pb_channel.push_note(self.config.get('PUSHBULLET', 'TITLE'), landed_message)
                self.pb_channel.push_file(**map_data)
            #Twitter
            if self.config.getboolean('TWITTER', 'ENABLE'):
                twitter_media_map_obj = self.tweet_api.media_upload(self.map_file_name)
                alt_text = "Call: " + self.callsign + " On Ground: " + str(self.on_ground) + " Alt: " + str(self.geo_alt_ft) + " Last Contact: " + str(time_since_contact) + " Trigger: " + self.trigger_type
                self.tweet_api.create_media_metadata(media_id= twitter_media_map_obj.media_id, alt_text= alt_text)
                self.tweet_api.update_status(status = ((self.twitter_title + " " + landed_message).strip()), media_ids=[twitter_media_map_obj.media_id])
                #self.tweet_api.update_with_media(self.map_file_name, status = (self.twitter_title + " " + landed_message).strip())
            self.takeoff_time = None
            self.landed_time = None
            self.time_since_tk = None
            os.remove(self.map_file_name)
            self.last_contact = None

#Set Variables to compare to next check
        self.last_feeding = self.feeding
        self.last_geo_alt_ft = self.geo_alt_ft
        self.last_on_ground = self.on_ground
        self.last_below_desired_ft = self.below_desired_ft
        self.last_longitude = self.longitude
        self.last_latitude = self.latitude


        if self.takeoff_time != None:
            self.elapsed_time = time.time() - self.takeoff_time
            self.time_since_tk = time.strftime("Time Since Take off  %H Hours : %M Mins : %S Secs", time.gmtime(self.elapsed_time))
            print(self.time_since_tk)
        self.printheader("foot")