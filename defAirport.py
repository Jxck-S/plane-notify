#https://www.geeksforgeeks.org/python-calculate-distance-between-two-places-using-geopy/
#https://openflights.org/data.html
def download_airports():
	import os
	if not os.path.isfile('airports.csv'):
		print("No airports.csv file, downloading now")
		try:
			import requests
			url = 'https://ourairports.com/data/airports.csv'
			airports = requests.get(url)
	
			open('airports.csv', 'wb').write(airports.content)
		except: 
			raise("Error getting airports.dat or storing")
		else:
			#Writes current date to airports.dat to show when it was aqquired 
			import datetime
			date = datetime.datetime.now()
			with open('airports.csv', 'a') as airports:
    				airports.write("#" + str(date))
			print("Successfully got airports.csv")
	elif os.path.isfile('airports.csv'):
			print("Already Have airports.csv, continuing")
#OLD Airport lookup
# def getClosestAirport(latitude, longitude):
# 	import csv
# 	from geopy.distance import geodesic
# 	plane = (latitude, longitude)
# 	header = ["id", "name", "city", "country", "iata", "icao",  "lat", "lng", "alt", "tz", "dst", "tz_db", "type", "source"]
# 	with open('airports.dat', encoding='utf-8') as airport_dat:
# 		airport_dat_reader = csv.DictReader(filter(lambda row: row[0]!='#', airport_dat), header)
# 		for airport in airport_dat_reader:
# 			airport_coord = float(airport['lat']), float(airport['lng'])
# 			airport_dist = float((geodesic(plane, airport_coord).mi))
# 			if "closest_airport_dict" not in locals():
# 				closest_airport_dict = airport
# 				closest_airport_dist = airport_dist
# 			elif airport_dist < closest_airport_dist:
# 				closest_airport_dict = airport
# 				closest_airport_dist = airport_dist
# 		closest_airport_dict['distance'] = closest_airport_dist
# 	print("Closest Airport:", closest_airport_dict['icao'], closest_airport_dict['name'], closest_airport_dist, "Miles Away")
# 	return closest_airport_dict
def getClosestAirport(latitude, longitude, allowed_types):
	import csv
	from geopy.distance import geodesic
	plane = (latitude, longitude)
	with open('airports.csv', 'r') as airport_csv:
		airport_csv_reader = csv.DictReader(filter(lambda row: row[0]!='#', airport_csv))
		for airport in airport_csv_reader:
			if airport['type'] in allowed_types:
				airport_coord = float(airport['latitude_deg']), float(airport['longitude_deg'])
				airport_dist = float((geodesic(plane, airport_coord).mi))
				if "closest_airport_dict" not in locals():
					closest_airport_dict = airport
					closest_airport_dist = airport_dist
				elif airport_dist < closest_airport_dist:
					closest_airport_dict = airport
					closest_airport_dist = airport_dist
		closest_airport_dict['distance'] = closest_airport_dist
		#Convert indent key to icao key as its labeled icao in other places not ident
		closest_airport_dict['icao'] = closest_airport_dict.pop('ident')
	print("Closest Airport:", closest_airport_dict['icao'], closest_airport_dict['name'], closest_airport_dist, "Miles Away")
	return closest_airport_dict