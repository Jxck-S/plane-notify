import requests
import json
import configparser
from datetime import datetime
from http.client import IncompleteRead
import http.client as http
import urllib3
main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')
def pullADSBX(planes):
    if len(planes) > 1:
                url = "https://adsbexchange.com/api/aircraft/json/"
    elif len(planes) == 1:
                url = "https://adsbexchange.com/api/aircraft/icao/" +    str(list(planes.keys())[0]) + "/"

    headers = {
                'api-auth': main_config.get('ADSBX', 'API_KEY'),
                'Accept-Encoding': 'gzip'
    }
    try:
        response = requests.get(url, headers = headers)
        response.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.RequestException) as error_message:
        print("Basic Connection Error")
        print(error_message)
        failed = True
        data = None
    except (IncompleteRead, http.IncompleteRead, ConnectionResetError, requests.ChunkEncodingError, urllib3.exceptions.ProtocolError, ValueError) as error_message:
        print("Connection Error")
        print(error_message)
        failed = True
        data = None
    except Exception as error_message:
        print("Connection Error uncaught, basic exception for all")
        print(error_message)
        failed = True
        data = None
    else:
        if "response" in locals() and response.status_code == 200:
            try:
                data = json.loads(response.text)
            except (json.decoder.JSONDecodeError, ValueError) as error_message:
                print("Error with JSON")
                print (json.dumps(data, indent = 2))
                print(error_message)
                failed = True
                data = None
            except TypeError as error_message:
                print("Type Error", error_message)
                failed = True
                data = None
            else:
                failed = False
        else:
            failed = True
            data = None
    if "response" in locals():
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


