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
    if main_config.getboolean('ADSBX', 'ENABLE_PROXY') is False:
        api_version = int(main_config.get('ADSBX', 'API_VERSION'))
        if api_version ==  1:
            if len(planes) > 1:
                        url = "https://adsbexchange.com/api/aircraft/json/"
            elif len(planes) == 1:
                        url = "https://adsbexchange.com/api/aircraft/icao/" +    str(list(planes.keys())[0]) + "/"
        elif api_version == 2:
            url = "https://adsbexchange.com/api/aircraft/v2/all"
        else:
            raise ValueError("No API Version set")
    else:
        if main_config.has_option('ADSBX', 'PROXY_HOST'):
            url = "http://" + main_config.get('ADSBX', 'PROXY_HOST') + ":8000/api/aircraft/v2/all"
        else:
            raise ValueError("Proxy enabled but no host")

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
    except (IncompleteRead, ConnectionResetError, urllib3.Exceptions, ValueError) as error_message:
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
                if 'data' in locals() and data != None:
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
        try:
            if data['msg'] != "No error":
                raise ValueError("Error from ADSBX: msg = ", data['msg'])
                failed = True
        except KeyError:
            pass
        data_ctime = float(data['ctime']) / 1000.0
        print("UTC of Data:",datetime.utcfromtimestamp(data_ctime))
        print("Current UTC:", datetime.utcnow())
    return data, failed