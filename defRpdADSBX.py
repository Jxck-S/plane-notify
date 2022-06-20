import requests
import json
import configparser
from datetime import datetime
from http.client import IncompleteRead

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
    except Exception as error:
            print('err.args:' + str(error.args))
            response = None
    if response is not None:
        try:
            data = json.loads(response.text)
        except (json.decoder.JSONDecodeError, ValueError) as error_message:
            print("Error with JSON")
            print(error_message)
            data = None
        except TypeError as error_message:
            print("Type Error", error_message)
            data = None
        else:
            if "msg" in data.keys() and data['msg'] != "No error":
                raise ValueError("Error from ADSBX: msg = ", data['msg'])
            if "ctime" in data.keys():
                data_ctime = float(data['ctime']) / 1000.0
                print("Data ctime:",datetime.utcfromtimestamp(data_ctime))
            if "now" in data.keys():
                data_now = float(data['now']) / 1000.0
                print("Data now time:",datetime.utcfromtimestamp(data_now))
        print("Current UTC:", datetime.utcnow())
    else:
        data = None
    return data
