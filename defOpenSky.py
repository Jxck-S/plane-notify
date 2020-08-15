def pullOpenSky(TRACK_PLANE):
    import configparser
    config = configparser.ConfigParser()
    config.read('config.ini')
    from opensky_api import OpenSkyApi
    planeData = None
    opens_api = OpenSkyApi(config.get('OPENSKY', 'USERNAME'), config.get('OPENSKY', 'PASSWORD'))
    failed = False
    try:
        planeData = opens_api.get_states(time_secs=0, icao24=TRACK_PLANE.lower())
    except:
            print ("OpenSky Error")
            failed = True
    if failed is False and planeData != None:
        plane_Dict = {}
        geo_alt_m = None
        for dataStates in planeData.states:
            plane_Dict['icao'] = (dataStates.icao24).upper()
            plane_Dict['callsign'] = (dataStates.callsign)
            plane_Dict['longitude'] = (dataStates.longitude)
            plane_Dict['latitude'] = (dataStates.latitude)
            plane_Dict['on_ground'] = (dataStates.on_ground)
            geo_alt_m = (dataStates.geo_altitude)
        try:
            if geo_alt_m != None:
                plane_Dict['geo_alt_ft'] = geo_alt_m  * 3.281
            elif plane_Dict['on_ground']:
                plane_Dict['geo_alt_ft'] = 0
        except KeyError:
            pass
        if plane_Dict == {}:
            plane_Dict = None
    else:
        plane_Dict = None
    return plane_Dict, failed