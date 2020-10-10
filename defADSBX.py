import requests
import json
import configparser
import time
from datetime import datetime
from http.client import IncompleteRead
main_config = configparser.ConfigParser()
main_config.read('mainconf.ini')
def pullADSBX(planes):
    if len(planes) > 1:
                url = "https://adsbexchange.com/api/aircraft/json/"
    elif len(planes) == 1:
                url = "https://adsbexchange.com/api/aircraft/icao/" +    str(list(planes.keys())[0]) + "/"

    headers = {
                'api-auth': main_config.get('ADSBX', 'API_KEY'),
                'Content-Encoding': 'gzip'
    }
    try:
        response = requests.get(url, headers = headers)
        data = response.text
        data = json.loads(data)
        failed = False
    except (requests.HTTPError,  requests.Timeout, IncompleteRead, ConnectionError, ConnectionResetError) as error_message:
        print("ADSBX Connection Error")
        print(error_message)
        failed = True
    except json.decoder.JSONDecodeError as error_message:
        print("Error with JSON")
        print (json.dumps(data, indent = 2))
        print(error_message)
        failed = True
    print ("HTTP Status Code:", response.status_code)
    if failed is False:
        data_ctime = float(data['ctime']) / 1000.0
        print("UTC of Data:",datetime.utcfromtimestamp(data_ctime))
        print("Current UTC:", datetime.utcnow())
        try:
            if data['msg'] == 'You need a key. Get a feeder or use pay API. https://rapidapi.com/adsbx/api/adsbexchange-com1':
                print("Bad auth", data['msg'])
                failed = True
        except KeyError:
            pass
    return data, failed


