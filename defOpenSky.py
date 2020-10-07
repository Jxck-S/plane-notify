def pullOpenSky(planes):
    import configparser
    main_config = configparser.ConfigParser()
    main_config.read('mainconf.ini')
    from opensky_api import OpenSkyApi
    planeData = None
    opens_api = OpenSkyApi(username= None if main_config.get('OPENSKY', 'USERNAME').upper() == "NONE" else main_config.get('OPENSKY', 'USERNAME'), password= None if main_config.get('OPENSKY', 'PASSWORD').upper() == "NONE" else main_config.get('OPENSKY', 'PASSWORD').upper())
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