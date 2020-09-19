import requests
import json
import configparser
import time
from datetime import datetime
config = configparser.ConfigParser()
config.read('config.ini')
def pullADSBX(icao):
	url = 'https://adsbexchange.com/api/aircraft/icao/' + icao + "/"
	headers = {
			'api-auth': config.get('ADSBX', 'API_KEY')
	}
	failed = False
	try:
		response = requests.get(url, headers = headers)
		data = response.text
		data = json.loads(data)
		#print (json.dumps(data, indent=4))
		print ("HTTP Status Code:", response.status_code)
	except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as error_message:
		print("ADSBX Connection Error")
		print(error_message)
		failed = True
		plane_Dict = None
	except json.decoder.JSONDecodeError as error_message:
		print("Error with JSON")
		print(error_message)
		failed = True
		plane_Dict = None
	if failed is False:
		ac = data['ac']
		ctime = data['ctime'] / 1000.0
		print("UTC of Data:",datetime.utcfromtimestamp(ctime))
		print("Current UTC:", datetime.utcnow())
		if ac != None:
			ac_dict = ac[0]
			try:
				plane_Dict = {'icao' : ac_dict['icao'], 'callsign' : ac_dict['call'], 'reg' : ac_dict['reg'], 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'geo_alt_ft' : int(ac_dict['galt']), 'on_ground' : bool(int(ac_dict["gnd"]))}
				if plane_Dict['on_ground']:
					plane_Dict['geo_alt_ft'] = 0
			except ValueError as e:
				plane_Dict = None
				failed = True
				print("Got data but some data is invalid!")
				print(e)
		else:
			plane_Dict = None

	return plane_Dict, failed




