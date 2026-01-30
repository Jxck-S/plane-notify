import requests
import json
import configparser
from datetime import datetime
from http.client import IncompleteRead
import urllib3
import socket
main_config = configparser.ConfigParser()
main_config.read('./configs/mainconf.ini')
def pull(url, headers):
    try:
        response = requests.get(url, headers = headers, timeout=30)
        print ("HTTP Status Code:", response.status_code)
        response.raise_for_status()
    except (requests.HTTPError, ConnectionError, requests.Timeout,  urllib3.exceptions.ConnectionError) as error_message:
        print("Basic Connection Error")
        print(error_message)
        response = None
    except (requests.RequestException, IncompleteRead, ValueError, socket.timeout, socket.gaierror) as error_message:
        print("Connection Error")
        print(error_message)
        response = None
    except Exception as error_message:
        print("Connection Error uncaught, basic exception for all")
        print(error_message)
        response = None
    return response

def pull_readsb(planes):
    if main_config.has_option('READSB', 'ENDPOINT'):
        url = main_config.get('READSB', 'ENDPOINT')
    else:
        raise ValueError("No endpoint set")
    headers = {
        "User-Agent": "plane-notify",
        'x-api-key': main_config.get('READSB', 'API_KEY'),
        'Accept-Encoding': 'gzip'
    }
    response = pull(url, headers)
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
                raise ValueError("Error from API: msg = ", data['msg'])
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



def pull_date_ras(date):
    home_url = main_config.get('READSB', 'RA_HOST')

    url = f"{home_url}/globe_history/{date}/acas/acas.json"
    headers = {
                'Accept-Encoding': 'gzip'
    }
    response = pull(url, headers)
    if response is not None:
        data = response.text.splitlines()
    else:
        data = None
    return data