"""
READSB Data Fetcher

This module handles the retrieval of aircraft data from a READSB-compatible API.
It includes functions to fetch current aircraft states and historical ACAS/TCAS resolution advisories.
"""

import configparser
import json
import socket
from datetime import UTC, datetime
from http.client import IncompleteRead

import requests
import urllib3

# Initialize configuration
main_config = configparser.ConfigParser()
main_config.read("./configs/mainconf.ini")


def pull(url, headers):
    """
    Performs a GET request to the specified URL with the given headers.

    Args:
        url (str): The URL to fetch data from.
        headers (dict): A dictionary of HTTP headers to include in the request.

    Returns:
        requests.Response or None: The response object if the request was successful,
                                   or None if an error occurred.
    """
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print("HTTP Status Code:", response.status_code)
        response.raise_for_status()
    except (
        requests.HTTPError,
        ConnectionError,
        requests.Timeout,
        urllib3.exceptions.ConnectionError,
    ) as error_message:
        print("Basic Connection Error")
        print(error_message)
        response = None
    except (
        TimeoutError,
        requests.RequestException,
        IncompleteRead,
        ValueError,
        socket.gaierror,
    ) as error_message:
        print("Connection Error")
        print(error_message)
        response = None
    except Exception as error_message:
        print("Connection Error uncaught, basic exception for all")
        print(error_message)
        response = None
    return response


def pull_readsb(planes):
    """
    Fetches the latest aircraft data from the READSB endpoint.

    Args:
        planes (list): A list of Plane objects (unused in current logic but kept for consistency/expansion).

    Returns:
        dict: A dictionary containing the parsed JSON data from ReadSB, or None if an error occurred.

    Raises:
        ValueError: If "ENDPOINT" is not set in the READSB configuration.
        ValueError: If the API returns an error message.
    """
    if main_config.has_option("READSB", "ENDPOINT"):
        url = main_config.get("READSB", "ENDPOINT")
    else:
        raise ValueError("No endpoint set")
    headers = {
        "User-Agent": "plane-notify",
        "x-api-key": main_config.get("READSB", "API_KEY"),
        "Accept-Encoding": "gzip",
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
            if "msg" in data.keys() and data["msg"] != "No error":
                raise ValueError("Error from API: msg = ", data["msg"])
            if "ctime" in data.keys():
                data_ctime = float(data["ctime"]) / 1000.0
                print("Data ctime:", datetime.utcfromtimestamp(data_ctime))
            if "now" in data.keys():
                data_now = float(data["now"]) / 1000.0
                print("Data now time:", datetime.utcfromtimestamp(data_now))
        print("Current UTC:", datetime.now(UTC))
    else:
        data = None
    return data


def pull_date_ras(date):
    """
    Fetches ACAS/TCAS Resolution Advisory (RA) data for a specific date.

    Args:
        date (str): The date string in "YYYY/MM/DD" format.

    Returns:
        list of str: A list of JSON strings, each representing an ACAS RA event,
                     or None if the request failed.
    """
    home_url = main_config.get("READSB", "RA_HOST")
    if not home_url:
        return None

    url = f"{home_url}/globe_history/{date}/acas/acas.json"
    headers = {"Accept-Encoding": "gzip"}
    response = pull(url, headers)
    if response is not None:
        data = response.text.splitlines()
    else:
        data = None
    return data
