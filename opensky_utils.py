from config import MAIN_CONFIG

from opensky_api import OpenSkyApi

USERNAME = MAIN_CONFIG.get("OPENSKY", "USERNAME")
PASSWORD = MAIN_CONFIG.get("OPENSKY", "PASSWORD")


def pull_opensky(planes):
    plane_data = None
    opens_api = OpenSkyApi(
        username=None if USERNAME.upper() == "NONE" else USERNAME,
        password=None if PASSWORD.upper() == "NONE" else PASSWORD.upper(),
    )
    failed = False
    icao_array = list(map(str.lower, planes.keys()))
    try:
        plane_data = opens_api.get_states(time_secs=0, icao24=icao_array)
    except Exception as e:
        print("OpenSky Error", e)
        failed = True
    return plane_data, failed
