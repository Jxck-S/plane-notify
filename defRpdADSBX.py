import requests
import configparser
from datetime import datetime

main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')
api_version = main_config.get('RpdADSBX', 'API_VERSION')

def pull_rpdadsbx(planes):
    api_version = int(main_config.get('RpdADSBX', 'API_VERSION'))
    if api_version != 2:
        raise ValueError("Bad RapidAPI ADSBX API Version")
    url = "https://adsbexchange-com1.p.rapidapi.com/v2/icao/" + planes + "/"
    headers = {
        "X-RapidAPI-Host": "adsbexchange-com1.p.rapidapi.com",
        "X-RapidAPI-Key": main_config.get('RpdADSBX', 'API_KEY')
    }
    try:
        response = requests.get(url, headers = headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "msg" in data.keys() and data['msg'] != "No error":
            raise ValueError("Error from ADSBX: msg = ", data['msg'])
        if "ctime" in data.keys():
            data_ctime = float(data['ctime']) / 1000.0
            print("Data ctime:",datetime.utcfromtimestamp(data_ctime))
        if "now" in data.keys():
            data_now = float(data['now']) / 1000.0
            print("Data now time:",datetime.utcfromtimestamp(data_now))
        print("Current UTC:", datetime.utcnow())
        return data
    except Exception as e:
        print('Error calling RapidAPI', e)
    return None
