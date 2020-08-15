def pullplane(TRACK_PLANE):
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    from opensky_api import OpenSkyApi
    opens_api = OpenSkyApi(config.get('OPENSKY', 'USERNAME'), config.get('OPENSKY', 'PASSWORD'))
    planeData = opens_api.get_states(time_secs=0, icao24=TRACK_PLANE.lower())
    return planeData