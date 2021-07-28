def pull_opensky(planes):
    import configparser
    main_config = configparser.ConfigParser()
    main_config.read('./configs/mainconf.ini')
    from opensky_api import OpenSkyApi
    planeData = None
    opens_api = OpenSkyApi(username= None if main_config.get('OPENSKY', 'USERNAME').upper() == "NONE" else main_config.get('OPENSKY', 'USERNAME'), password= None if main_config.get('OPENSKY', 'PASSWORD').upper() == "NONE" else main_config.get('OPENSKY', 'PASSWORD').upper())
    failed = False
    icao_array = []
    for key in planes.keys():
        icao_array.append(key.lower())
    try:
        planeData = opens_api.get_states(time_secs=0, icao24=icao_array)
    except Exception as e:
            print ("OpenSky Error", e)
            failed = True
    return planeData, failed