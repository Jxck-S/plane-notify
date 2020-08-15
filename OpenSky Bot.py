#Github Updated - NotifyBot 9
#Import Modules
#Setup Geopy
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="OpenSkyBot", timeout=5)

import json
import time
from colorama import Fore, Back, Style 
import datetime
from defOpenSky import pullplane
from defMap import getMap

#Setup PushBullet
from pushbullet import Pushbullet
pb = Pushbullet("<pushbulletapikey>")
pb_channel = pb.get_channel('<channeltaghere>')

#Setup Tweepy
from defTweet import tweepysetup
tweet_api = tweepysetup()
#Set Plane ICAO
TRACK_PLANE = '<planeicaohere>' 
icao = TRACK_PLANE.upper()
#Pre Set Variables
geo_altitude = None
geo_alt_ft = None
last_geo_alt_ft = None
last_below_desired_ft = None
feeding = None
last_feeding = None   
last_on_ground = None
on_ground = None
invalid_Location = None
longitude = None
latitude = None
geo_alt_m = None
running_Count = 0
callsign = None
takeoff_time = None
#Begin Looping program
while True:
    running_Count += 1
    start_time = time.time()
    print (Back.MAGENTA, "--------", running_Count, "-------------------------------------------------------------", Style.RESET_ALL)
#Reset Variables
    below_desired_ft = None
    geo_alt_ft = None
    longitude = None
    latitude = None
    on_ground = None
    geo_alt_m = None
#Get API States for Plane
    planeData = None
    try:
        planeData = pullplane(TRACK_PLANE)
    except:
        print ("Opensky Error")
    print (Fore.YELLOW)
    print ("OpenSky Debug", planeData)
    print(Style.RESET_ALL) 

#Pull Variables from planeData
    if planeData != None:
        for dataStates in planeData.states:
            icao = (dataStates.icao24)
            callsign = (dataStates.callsign)
            longitude = (dataStates.longitude)
            latitude = (dataStates.latitude)
            on_ground = (dataStates.on_ground)           
            geo_alt_m = (dataStates.geo_altitude)
        if geo_alt_m != None:
	        geo_alt_ft = geo_alt_m  * 3.281
        elif geo_alt_m == None and on_ground:
            geo_alt_ft = 0 
        print (Fore.CYAN)
        print ("ICAO: ", icao)
        print ("Callsign: ", callsign)
        print ("On Ground: ", on_ground)
        print ("Latitude: ", latitude)
        print ("Longitude: ", longitude)
        print ("GEO Alitude Ft: ", geo_alt_ft)

    #Lookup Location of coordinates 
        if longitude != None and latitude != None:

            combined = f"{latitude}, {longitude}"
            try:
                location = geolocator.reverse(combined)
            except:
                print ("Geopy API Error")
            print (Fore.YELLOW)
            print ("Geopy debug: ", location.raw)
            print(Style.RESET_ALL) 
            feeding = True 
        else:
            print (Fore.RED + 'Not Feeding')
            feeding = False
            print(Style.RESET_ALL) 

    #Figure if valid location, valid being geopy finds a location
        if feeding:
            try:
                geoError = location.raw['error']
            except KeyError:
                invalid_Location = False
                geoError = None
            else:
                invalid_Location = True

            print ("Invalid Location: ", invalid_Location)
        
            if invalid_Location:
                print (Fore.RED)
                print (geoError)
                print ("Likely Over Water or Invalid Location")
                print(Style.RESET_ALL)
            

        #Convert Full address to sep variables only if Valid Location
            elif invalid_Location is False:
                address = location.raw['address']
                country = address.get('country', '')
                country_code = address.get('country_code', '').upper()
                state = address.get('state', '')
                county = address.get('county', '')
                city = address.get('city', '')
                town = address.get('town', '')
                hamlet = address.get('hamlet', '')
                
                
    #           print (Fore.YELLOW)
    #           print ("Address Fields debug: ", address)
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
        
#Check if below desire ft
        if geo_alt_ft is None:
            below_desired_ft = False
        elif geo_alt_ft < 10000:
            below_desired_ft = True
#Check if tookoff
        tookoff = bool(invalid_Location is False and below_desired_ft and on_ground is False and ((last_feeding is False and feeding) or (last_on_ground)))
        print ("Tookoff Just Now:", tookoff)
        

#Check if Landed
        landed = bool(last_below_desired_ft and invalid_Location is False and ((last_feeding and feeding is False and last_on_ground is False)  or (on_ground and last_on_ground is False)))
        print ("Landed Just Now:", landed)
    
    #Chose city town county or hamlet for location as not all are always avalible. 
        if feeding and invalid_Location is False:
            aera_hierarchy = city or town or county or hamlet 
    #Takeoff Notifcation and Landed
        if tookoff:
            tookoff_message = ("Just took off from" + " " + aera_hierarchy + ", " + state + ", " + country_code)
            print (tookoff_message)
            getMap(aera_hierarchy + ", "  + state + ", "  + country_code)
            with open("map.png", "rb") as pic:
                map_data = pb.upload_file(pic, "Tookoff")
            push = pb_channel.push_note("title", tookoff_message)
            push = pb_channel.push_file(**map_data)
            tweet_api.update_with_media("map.png", status = tookoff_message)
            takeoff_time = time.time()



        if landed: 
            landed_time_msg = ""
            if takeoff_time != None:
                landed_time = time.time() - takeoff_time
                landed_time_msg = time.strftime("Apx. flt. time %H Hours : %M Mins ", time.gmtime(landed_time))
            landed_message = ("Landed just now in" + " " + aera_hierarchy + ", " + state + ", " + country_code + ". " + landed_time_msg)
            print (landed_message)
            getMap(aera_hierarchy + ", "  + state + ", "  + country_code)
            with open("map.png", "rb") as pic:
                map_data = pb.upload_file(pic, "Landed")
            push = pb_channel.push_note("title", landed_message)
            push = pb_channel.push_file(**map_data)
            tweet_api.update_with_media("map.png", status = landed_message)
            takeoff_time = None
            landed_time = None
            time_since_tk = None
            
#Set Variables to compare to next check
        last_feeding = feeding
        last_geo_alt_ft = geo_alt_ft
        last_on_ground = on_ground
        last_below_desired_ft = below_desired_ft

    else:
        print ("Rechecking OpenSky")
        planeDataMSG = str(planeData)
    if takeoff_time != None:
        elapsed_time = time.time() - takeoff_time
        time_since_tk = time.strftime("Time Since Take off %H Hours : %M Mins : %S Secs", time.gmtime(elapsed_time))
        print(time_since_tk)


   
    elapsed_calc_time = time.time() - start_time

    print (Back.MAGENTA, "--------", running_Count, "------------------------Elapsed Time- ", elapsed_calc_time, "-------------------------------------", Style.RESET_ALL)
    print ("")
    time.sleep(15)


