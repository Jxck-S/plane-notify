import json
import requests
def get_avg_fuel_price():
	import pandas as pd
	from bs4 import BeautifulSoup
	try:
		response = requests.get("https://www.airnav.com/fuel/report.html")
		soup = BeautifulSoup(response.text, 'lxml') # Parse the HTML as a string
		table = soup.find_all('table')[3] # Grab the first table
		nation_wide = table.find_all('tr')[4]
		nation_wide_avg_jeta = nation_wide.find_all('td')[6]
		print("Current nationwide Jet-A fuel price avg per G is $", nation_wide_avg_jeta.text[1:])
		return(float(nation_wide_avg_jeta.text[1:]))
	except Exception as e:
		print(e)
		return None
	
def fuel_calculation(aircraft_icao_type, minutes):
	"""Calculates fuel usage, price, c02 output of a flight depending on aircraft type and flight length"""
	with open("aircraft_type_fuel_consumption_rates.json", "r") as f:
		fuellist = json.loads(f.read())
	#avg_fuel_price_per_gallon = 5.08
	fuel_flight_info = {}
	if aircraft_icao_type in fuellist.keys():
		avg_fuel_price_per_gallon = get_avg_fuel_price()
		galph = fuellist[aircraft_icao_type]["galph"]
		fuel_used_gal = round(galph * (minutes/60), 2)
		fuel_flight_info["fuel_price"] = round(fuel_used_gal * avg_fuel_price_per_gallon)
		fuel_used_kg = fuel_used_gal * 3.04
		c02_tons = round((fuel_used_kg * 3.15 ) / 907.185)
		fuel_flight_info['fuel_used_kg'] = round(fuel_used_kg)
		fuel_flight_info["fuel_used_gal"] = round(fuel_used_gal)
		fuel_flight_info['fuel_used_lters'] = round(fuel_used_gal*3.78541)
		fuel_flight_info["fuel_used_pds"] = round(fuel_used_kg * 2.20462)
		fuel_flight_info["c02_tons"] = c02_tons
		print ("Fuel info", fuel_flight_info)
		return fuel_flight_info
	else:
		print("Can't calculate fuel info unknown aircraft ICAO type")
		return None

def fuel_message(fuel_info):
	cost = "{:,}".format(fuel_info['fuel_price'])
	gallons = "{:,}".format(fuel_info['fuel_used_gal'])
	lters = "{:,}".format(fuel_info['fuel_used_lters'])
	pds = "{:,}".format(fuel_info['fuel_used_pds'])
	kgs = "{:,}".format(fuel_info['fuel_used_kg'])
	fuel_message = f"~ {gallons} gallons ({lters} liters). \n~ {pds} pds ({kgs} kg) of jet fuel used. \n~ ${cost} cost of fuel. \n~ {fuel_info['c02_tons']} tons of CO2 emissions."
	print(fuel_message)
	return fuel_message
#fuel_info = fuel_calculation("B738", 180)
#fuel_message(fuel_info)
