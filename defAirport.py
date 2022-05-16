import csv
import math
def add_airport_region(airport_dict):
	#Get full region/state name from iso region name
	with open('./dependencies/regions.csv', 'r', encoding='utf-8') as regions_csv:
		regions_csv = csv.DictReader(filter(lambda row: row[0]!='#', regions_csv))
		for region in regions_csv:
			if region['code'] == airport_dict['iso_region']:
				airport_dict['region'] = region['name']
	return airport_dict
def getClosestAirport(latitude, longitude, allowed_types):
	from geopy.distance import geodesic
	plane = (latitude, longitude)
	with open('./dependencies/airports.csv', 'r', encoding='utf-8') as airport_csv:
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
		closest_airport_dict['icao'] = closest_airport_dict.pop('gps_code')
		closest_airport_dict = add_airport_region(closest_airport_dict)
	return closest_airport_dict
def get_airport_by_icao(icao):
	with open('./dependencies/airports.csv', 'r', encoding='utf-8') as airport_csv:
		airport_csv_reader = csv.DictReader(filter(lambda row: row[0]!='#', airport_csv))
		for airport in airport_csv_reader:
			if airport['gps_code'] == icao:
				matching_airport = airport
				#Convert indent key to icao key as its labeled icao in other places not ident
				matching_airport['icao'] = matching_airport.pop('gps_code')
				break
		matching_airport = add_airport_region(matching_airport)
		return matching_airport