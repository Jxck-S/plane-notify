class Plane:
    def __init__(self, icao, conf_file):
        self.icao = icao.upper()
        self.conf_file = conf_file
        self.geo_alt_ft = None
        self.last_geo_alt_ft = None
        self.last_below_desired_ft = None
        self.feeding = None
        self.last_feeding = None
        self.last_on_ground = None
        self.on_ground = None
        self.invalid_Location = None
        self.longitude = None
        self.latitude = None
        self.callsign = None
        self.takeoff_time = None
        self.reg = None
        self.map_file_name = icao.upper() + "_map.png"
        self.last_latitude = None
        self.last_longitude = None
        self.recheck_needed = None
        self.last_recheck_needed = None
    def getICAO(self):
        return self.icao
    def run(self, ac_dict):

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
        #Setup Config File
        import configparser
        self.config = configparser.ConfigParser()
        self.config.read(self.conf_file)
        main_config = configparser.ConfigParser()
        main_config.read('mainconf.ini')

        #Platform for determining OS for strftime
        import platform

        if self.config.getboolean('GOOGLE', 'STATICMAP_ENABLE'):
            from defMap import getMap
        else:
            from defSS import getSS

        if self.config.getboolean('DISCORD', 'ENABLE'):
            from defDiscord import sendDis
        #Setup Tweepy
        if self.config.getboolean('TWITTER', 'ENABLE'):
            from defTweet import tweepysetup
            self.tweet_api = tweepysetup(self.conf_file)
        #Setup PushBullet
        if self.config.getboolean('PUSHBULLET', 'ENABLE'):
            from pushbullet import Pushbullet
            self.pb = Pushbullet(self.config['PUSHBULLET']['API_KEY'])
            self.pb_channel = self.pb.get_channel(self.config.get('PUSHBULLET', 'CHANNEL_TAG'))

        print (Back.MAGENTA, "---------", self.conf_file, "---------------------------- ICAO:", self.icao, "--------------------------", Style.RESET_ALL)
    #Reset Variables
        self.below_desired_ft = None
        self.geo_alt_ft = None
        self.longitude = None
        self.latitude = None
        self.on_ground = None
        self.has_location = None
    #Get States from ADSBX or OPENS Vector
        self.plane_Dict = None
        if main_config.get('DATA', 'SOURCE') == "OPENS":
            self.val_error = False
            if ac_dict != None:
                try:
                    self.plane_Dict ={'icao' : ac_dict.icao24, 'callsign' : ac_dict.callsign, 'latitude' : ac_dict.latitude, 'longitude' : ac_dict.longitude,  'on_ground' : bool(ac_dict.on_ground)}
                    if ac_dict.geo_altitude != None:
                        self.plane_Dict['geo_alt_ft'] = float(ac_dict.geo_altitude)  * 3.281
                    elif self.plane_Dict['on_ground']:
                        self.plane_Dict['geo_alt_ft'] = 0
                except ValueError as e:
                    self.plane_Dict = None
                    self.val_error = True
                    print("Got data but some data is invalid!")
                    print(e)
            else:
                self.plane_Dict = None

            print (Fore.YELLOW)
            print ("OpenSky Sourced Data: ", self.plane_Dict)
            print(Style.RESET_ALL)

        elif main_config.get('DATA', 'SOURCE') == "ADSBX":
            self.val_error = False
            if ac_dict != None:
                try:
                    self.plane_Dict = {'icao' : ac_dict['icao'], 'callsign' : ac_dict['call'], 'reg' : ac_dict['reg'], 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'geo_alt_ft' : int(ac_dict['galt']), 'on_ground' : bool(int(ac_dict["gnd"]))}
                    if self.plane_Dict['on_ground']:
                        self.plane_Dict['geo_alt_ft'] = 0
                except ValueError as e:
                    self.plane_Dict = None
                    self.val_error = True
                    print("Got data but some data is invalid!")
                    print(e)
            else:
                self.plane_Dict = None

            print (Fore.YELLOW)
            print ("ADSBX Sourced Data: ", self.plane_Dict)
            print(Style.RESET_ALL)
            print (Fore.CYAN)
            print ("ICAO:", self.icao)
            print(Style.RESET_ALL)


        if self.val_error is False:
            if self.plane_Dict == None:
                self.feeding = False
            elif self.plane_Dict != None:
                self.feeding = True
                self.__dict__.update(self.plane_Dict)
                print (Fore.CYAN)
                if main_config.get('DATA', 'SOURCE') == "ADSBX":
                    print("Registration: ", self.reg)
                print ("Callsign: ", self.callsign)
                print ("On Ground: ", self.on_ground)
                print ("Latitude: ", self.latitude)
                print ("Longitude: ", self.longitude)
                print ("GEO Alitude Ft: ", self.geo_alt_ft)
                print(Style.RESET_ALL)
        #Set Check for inconsistancy in data
            if not self.last_recheck_needed:
                #Recheck needed if feeding state changes
                if self.feeding == False  and self.last_feeding:
                    self.recheck_needed = True
                    print("Recheck needed, feeding status changed")
                else:
                    self.recheck_needed = False
            elif self.last_recheck_needed:
                self.recheck_needed = False


            #Run a Check compares new data to last flagged(check) data
            if self.last_recheck_needed:
                if self.recheck_feeding == self.feeding:
                    print("Data Feeding change Consistent")
                elif self.recheck_feeding != self.feeding:
                    print("Data Feeding change was Inconsistent last data ignored")

            self.recheck_feeding = self.feeding
            self.last_recheck_needed = self.recheck_needed

            if self.recheck_needed is False:

        #Check if below desire ft
                if self.geo_alt_ft is None:
                    self.below_desired_ft = False
                elif self.geo_alt_ft < 10000:
                    self.below_desired_ft = True
        #Check if tookoff
                if self.below_desired_ft and self.on_ground is False:
                    if self.last_on_ground:
                        self.tookoff = True
                        self.trigger_type = "no longer on ground"
                        self.tookoff_header = "Took off from "
                    elif self.last_feeding is False and self.feeding:
                        self.tookoff = True
                        self.trigger_type = "data acquisition"
                        self.tookoff_header = "Took off near "
                    else:
                        self.tookoff = False
                else:
                    self.tookoff = False

                #self.tookoff = bool(self.below_desired_ft and self.on_ground is False and ((self.last_feeding is False and self.feeding) or (self.last_on_ground)))
                print ("Tookoff Just Now:", self.tookoff)


        #Check if Landed
                if self.last_below_desired_ft:
                    if self.on_ground and self.last_on_ground is False:
                        self.landed = True
                        self.trigger_type = "now on ground"
                        self.landed_header = "Landed in "
                    elif self.last_feeding and self.feeding is False and self.last_on_ground is False:
                        self.landed = True
                        self.trigger_type = "data loss"
                        self.landed_header = "Landed near "
                    else:
                        self.landed = False
                else:
                    self.landed = False
                    
                #self.landed = bool(self.last_below_desired_ft  and ((self.last_feeding and self.feeding is False and self.last_on_ground is False)  or (self.on_ground and self.last_on_ground is False)))
                print ("Landed Just Now:", self.landed)
                if self.landed or self.tookoff:
                    print ("Trigger Type:", self.trigger_type)

        #Lookup Location of coordinates
                if self.landed or self.tookoff:
                    if self.landed and self.last_longitude != None and self.last_latitude != None:
                        self.combined = f"{self.last_latitude}, {self.last_longitude}"
                        self.has_coords = True
                    elif self.tookoff and self.longitude != None and self.latitude != None:
                        self.combined =  f"{self.latitude} , {self.longitude}"
                        self.has_coords = True
                    else:
                        print (Fore.RED + 'No Location')
                        self.has_location = False
                        self.invalid_Location = True
                        self.has_coords = False
                        print(Style.RESET_ALL)
                    if self.has_coords:
                        try:
                            self.location = geolocator.reverse(self.combined)
                        except:
                            print ("Geopy API Error")
                        else:
                #           print (Fore.YELLOW, "Geopy debug: ", location.raw, Style.RESET_ALL)
                            self.has_location = True




            #Figure if valid location, valid being geopy finds a location
                if self.has_location:
                    try:
                        self.geoError = self.location.raw['error']
                    except KeyError:
                        self.invalid_Location = False
                        self.geoError = None
                    else:
                        self.invalid_Location = True

                    print ("Invalid Location: ", self.invalid_Location)

                    if self.invalid_Location:
                        print (Fore.RED)
                        print (self.geoError)
                        print ("Likely Over Water or Invalid Location")
                        print(Style.RESET_ALL)


                #Convert Full address to sep variables only if Valid Location
                    elif self.invalid_Location is False:
                        self.address = self.location.raw['address']
                        self.country = self.address.get('country', '')
                        self.country_code = self.address.get('country_code', '').upper()
                        self.state = self.address.get('state', '')
                        self.county = self.address.get('county', '')
                        self.city = self.address.get('city', '')
                        self.town = self.address.get('town', '')
                        self.hamlet = self.address.get('hamlet', '')
            #           print (Fore.YELLOW)
            #           print ("Address Fields debug: ", self.address)
            #           print(Style.RESET_ALL)
                        print (Fore.GREEN)
                        print("Entire Address: ", self.location.address)
                        print ("Country Code: ", self.country_code)
                        print ("Country: ", self.country)
                        print ("State: ", self.state)
                        print ("City: ", self.city)
                        print ("Town: ", self.town)
                        print ("Hamlet: ", self.hamlet)
                        print ("County: ", self.county)
                        print(Style.RESET_ALL)
            #Chose city town county or hamlet for location as not all are always avalible.
                if self.invalid_Location is False:
                    self.aera_hierarchy = self.city or self.town or self.county or self.hamlet
            #Set Discord Title
                if self.config.getboolean('DISCORD', 'ENABLE'):
                    self.dis_title = self.icao if self.config.get('DISCORD', 'TITLE') == "icao" else self.callsign if self.config.get('DISCORD', 'TITLE') == "callsign" else self.config.get('DISCORD', 'TITLE')

            #Takeoff Notifcation and Landed
                if self.tookoff:
                    if self.invalid_Location is False:
                        self.tookoff_message = (self.tookoff_header  + self.aera_hierarchy + ", " + self.state + ", " + self.country_code)
                    else:
                        self.tookoff_message = ("Took off")
                    print (self.tookoff_message)
                    #Google Map or tar1090 screenshot
                    if self.config.getboolean('GOOGLE', 'STATICMAP_ENABLE'):
                        getMap(self.aera_hierarchy + ", "  + self.state + ", "  + self.country_code)
                    else:
                        getSS(self.icao)
                    #Discord
                    if self.config.getboolean('DISCORD', 'ENABLE'):
                        self.dis_message = self.dis_title + " "  + self.tookoff_message
                        sendDis(self.dis_message, self.map_file_name, self.conf_file)
                    #PushBullet
                    if self.config.getboolean('PUSHBULLET', 'ENABLE'):
                        with open(self.map_file_name, "rb") as pic:
                            map_data = self.pb.upload_file(pic, "Tookoff IMG")
                        push = self.pb_channel.push_note(self.config.get('PUSHBULLET', 'TITLE'), self.tookoff_message)
                        push = self.pb_channel.push_file(**map_data)
                    #Twitter
                    if self.config.getboolean('TWITTER', 'ENABLE'):
                        self.tweet_api.update_with_media(self.map_file_name, status = self.tookoff_message)
                    self.takeoff_time = time.time()
                    os.remove(self.map_file_name)


                if self.landed:
                    self.landed_time_msg = ""
                    if self.takeoff_time != None:
                        self.landed_time = time.time() - self.takeoff_time
                        if platform.system() == "Linux":
                            self.landed_time_msg = time.strftime("Apx. flt. time %-H Hours : %-M Mins ", time.gmtime(self.landed_time))
                        elif platform.system() == "Windows":
                            self.landed_time_msg = time.strftime("Apx. flt. time %#H Hours : %#M Mins ", time.gmtime(self.landed_time))
                    if self.invalid_Location is False:
                        self.landed_message = (self.landed_header + self.aera_hierarchy + ", " + self.state + ", " + self.country_code + ". " + self.landed_time_msg)
                    else:
                        self.landed_message = ("Landed", self.landed_time_msg)
                    print (self.landed_message)
                    #Google Map or tar1090 screenshot
                    if self.config.getboolean('GOOGLE', 'STATICMAP_ENABLE'):
                        getMap(self.aera_hierarchy + ", "  + self.state + ", "  + self.country_code)
                    else:
                        getSS(self.icao)
                    #Discord
                    if self.config.getboolean('DISCORD', 'ENABLE'):
                        self.dis_message =  self.dis_title + " "  + self.landed_message
                        sendDis(self.dis_message, self.map_file_name, self.conf_file)
                    #PushBullet
                    if self.config.getboolean('PUSHBULLET', 'ENABLE'):
                        with open(self.map_file_name, "rb") as pic:
                            map_data = self.pb.upload_file(pic, "Landed IMG")
                        push = self.pb_channel.push_note(self.config.get('PUSHBULLET', 'TITLE'), self.landed_message)
                        push = self.pb_channel.push_file(**map_data)
                    #Twitter
                    if self.config.getboolean('TWITTER', 'ENABLE'):
                        self.tweet_api.update_with_media(self.map_file_name, status = self.landed_message)
                    self.takeoff_time = None
                    self.landed_time = None
                    self.time_since_tk = None
                    os.remove(self.map_file_name)

        #Set Variables to compare to next check
                self.last_feeding = self.feeding
                self.last_geo_alt_ft = self.geo_alt_ft
                self.last_on_ground = self.on_ground
                self.last_below_desired_ft = self.below_desired_ft
                self.last_longitude = self.longitude
                self.last_latitude = self.latitude

        elif self.val_error:
            print ("Failed to Parse Will Recheck this Plane After new data")

        if self.takeoff_time != None:
            self.elapsed_time = time.time() - self.takeoff_time
            self.time_since_tk = time.strftime("Time Since Take off  %H Hours : %M Mins : %S Secs", time.gmtime(self.elapsed_time))
            print(self.time_since_tk)




        print (Back.MAGENTA, "---------------------------------------------------------------------------", Style.RESET_ALL)
