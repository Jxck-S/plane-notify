#https://www.geeksforgeeks.org/python-calculate-distance-between-two-places-using-geopy/
#https://openflights.org/data.html
def download_airports():
	import os
	if not os.path.isfile('airports.dat'):
		print("No airports.dat file, downloading now")
		try:
			import requests
			url = 'https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat'
			airports = requests.get(url)
	
			open('airports.dat', 'wb').write(airports.content)
		except: 
			raise("Error getting airports.dat or storing")
		else:
			#Writes current date to airports.dat to show when it was aqquired 
			import datetime
			date = datetime.datetime.now()
			with open('airports.dat', 'a') as airports:
    				airports.write("#" + str(date))
			print("Successfully got airports.dat")
	elif os.path.isfile('airports.dat'):
			print("Already Have airports.dat, continuing")
def getClosestAirport(latitude, longitude):
		import json
		import csv
		from geopy.distance import geodesic
		plane = (latitude, longitude)
		header = ["id", "name", "city", "country", "iata", "icao",  "lat", "lng", "alt", "tz", "dst", "tz_db", "type", "source"]
		airports = []
		first_run = True
		with open('airports.dat', encoding='utf-8') as csvf:
				reader = csv.DictReader(filter(lambda row: row[0]!='#', csvf), header)
				#for row in reader:
				#    airports.append(row)
				for row in reader:
						airport = row
						airport_coord = float(airport['lat']), float(airport['lng'])
						airport_dist = float((geodesic(plane, airport_coord).mi))
						if first_run:
								closest_airport_dict = airport
								closest_airport_dist = airport_dist
								first_run = False
						elif airport_dist < closest_airport_dist:
								closest_airport_dict = airport
								closest_airport_dist = airport_dist
				closest_airport_dict['distance'] = closest_airport_dist
				print("Closest Airport:", closest_airport_dict['icao'], closest_airport_dict['name'], closest_airport_dist, "Miles Away")
		return closest_airport_dict