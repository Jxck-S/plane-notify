#https://www.geeksforgeeks.org/python-calculate-distance-between-two-places-using-geopy/
#https://openflights.org/data.html
def getAirport(latitude, longitude):
    import json
    import csv
    from geopy.distance import geodesic
    plane = (latitude, longitude)
    header = ["id", "name", "city", "country", "iata", "icao",  "lat", "lng", "alt", "tz", "dst", "tz_db", "type", "source"]
    airports = []
    first_run = True
    with open('airports.dat', encoding='utf-8') as csvf:
        reader = csv.DictReader( csvf, header)
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
        print("Closest Airport:", closest_airport_dict['icao'], closest_airport_dict['name'], closest_airport_dist, "Miles Away")
    return closest_airport_dict