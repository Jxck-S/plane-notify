#Import Modules
#Setup Geopy
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="*", timeout=5)

import json
import time
from colorama import Fore, Back, Style 

#Setup PushBullet
from pushbullet import Pushbullet
pb = Pushbullet("*")
elon_jet_channel = pb.get_channel('<channel tag here>')

#Setup OpenSKy
from opensky_api import OpenSkyApi
opens_api = OpenSkyApi("*", "*")

#Set Plane ICAO
TRACK_PLANE = 'A5B1A8' 
#Pre Set Variables
geo_altitude = None
geo_alt_ft = None
last_geo_alt_ft = None
last_below_10k_ft = None
below_10k_ft = None
feeding = None
last_feeding = None   
last_on_ground = None
on_ground = None
invalid_Location = None
longitude = None
latitude = None
geo_alt_m = None
running_Count = 0
icao = None
callsign = None
#Begin Looping program
while True:
    running_Count += 1
    print (Back.MAGENTA, "--------", running_Count, "-------------------------------------------------------------", Style.RESET_ALL)
#Reset Variables
    geo_alt_ft = None
    longitude = None
    latitude = None
    on_ground = None
    geo_alt_m = None
#Get API States for Plane
    planeData = None
    planeData = opens_api.get_states(time_secs=0, icao24=TRACK_PLANE.lower())
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
        if geo_alt_m == None and on_ground:
	        geo_alt_ft = 0 
        elif geo_alt_m != None :
	        geo_alt_ft = geo_alt_m  * 3.281
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
            location = geolocator.reverse(combined)
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
                state = address.get('state', '')
                county = address.get('county', '')
                city = address.get('city', '')
                
                
    #           print (Fore.YELLOW)
    #           print ("Address Fields debug: ", address)
    #           print(Style.RESET_ALL)
                print (Fore.GREEN)
                print("Entire Address: ", location.address)
                print ()
                print ("Country: ", country)
                print ("State: ", state)
                print ("City: ", city)
                print ("County: ", county)
                print(Style.RESET_ALL)

#Check if below 10k ft
        if geo_alt_ft is None:
            below_10k_ft = False
        elif geo_alt_ft < 10000:
            below_10k_ft = True
#Check if tookoff
        tookoff = bool(last_feeding is False and feeding and on_ground is False and invalid_Location is False and below_10k_ft)
        print ("Tookoff Just Now:", tookoff)

#Check if Landed
        landed = bool((last_feeding and feeding is False and invalid_Location is False and (on_ground or last_below_10k_ft)) or (on_ground and last_on_ground is False))
        print ("Landed Just Now:", landed)
        

    #Takeoff Notifcation and Landed
        if tookoff:
            tookoff_message = ("Just took off from" + " " + (city or county) + ", " + state + ", " + country)
            print (tookoff_message)
            push = elon_jet_channel.push_note("*", tookoff_message)

        if landed:
            landed_message = ("Landed just now at" + " " + (city or county) + ", " + state + ", " + country)
            print (landed_message)
            push = elon_jet_channel.push_note("*", landed_message)
            

   
#Set Variables to compare to next check
        last_feeding = feeding
        last_geo_alt_ft = geo_alt_ft
        last_on_ground = on_ground
        last_below_10k_ft = below_10k_ft

    else:
        print ("Rechecking OpenSky")
        planeDataMSG = str(planeData)


    print (Back.MAGENTA, "--------", running_Count, "-------------------------------------------------------------", Style.RESET_ALL)
    print ("")
    time.sleep(15)


