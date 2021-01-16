#https://www.geeksforgeeks.org/python-calculate-distance-between-two-places-using-geopy/
#https://openflights.org/data.html

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
	with open('airports.csv', 'r', encoding='utf-8') as airport_csv:
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
		closest_airport_dict['distance_mi'] = closest_airport_dist
		#Convert indent key to icao key as its labeled icao in other places not ident
		closest_airport_dict['icao'] = closest_airport_dict.pop('ident')
	#Get full region/state name from iso region name
	with open('regions.csv', 'r', encoding='utf-8') as regions_csv:
		regions_csv = csv.DictReader(filter(lambda row: row[0]!='#', regions_csv))
		for region in regions_csv:
			if region['code'] == closest_airport_dict['iso_region']:
				closest_airport_dict['region'] = region['name']
	return closest_airport_dict