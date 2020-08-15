import requests
import json
import configparser
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
  except:
    print("ADSBX Error")
    failed = True
    plane_Dict = None
  if failed is False:
    ac = data['ac']
    if ac != None:
      ac_dict = ac[0]
      plane_Dict = {'icao' : ac_dict['icao'], 'callsign' : ac_dict['call'], 'reg' : ac_dict['reg'], 'latitude' : float(ac_dict['lat']), 'longitude' : float(ac_dict['lon']), 'geo_alt_ft' : int(ac_dict['galt']), 'on_ground' : bool(int(ac_dict["gnd"]))}
      if plane_Dict['on_ground']:
        plane_Dict['geo_alt_ft'] = 0
    else:
      plane_Dict = None

  return plane_Dict, failed




