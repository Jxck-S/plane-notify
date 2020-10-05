def pullOpenSky(planes):
    import configparser
    config = configparser.ConfigParser()
    config.read('mainconf.ini')
    from opensky_api import OpenSkyApi
    planeData = None
    opens_api = OpenSkyApi(config.get('OPENSKY', 'USERNAME'), config.get('OPENSKY', 'PASSWORD'))
    failed = False
    icao_array = []
    for key, obj in planes.items():
        icao_array.append(key.lower())
    try:
        planeData = opens_api.get_states(time_secs=0, icao24=icao_array)
    except:
            print ("OpenSky Error")
            failed = True
    return planeData, failed