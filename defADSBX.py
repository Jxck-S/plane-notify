import requests
import json
import configparser
import time
from datetime import datetime
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
        print ("HTTP Status Code:", response.status_code)
        failed = False
    except (requests.HTTPError, requests.ConnectionError, requests.Timeout) as error_message:
        print("ADSBX Connection Error")
        print(error_message)
        failed = True
    except json.decoder.JSONDecodeError as error_message:
        print("Error with JSON")
        print (json.dumps(data, indent = 2))
        print(error_message)
        failed = True
    if failed is False:
        data_ctime = data['ctime'] / 1000.0
        print("UTC of Data:",datetime.utcfromtimestamp(data_ctime))
        print("Current UTC:", datetime.utcnow())
    return data, failed


