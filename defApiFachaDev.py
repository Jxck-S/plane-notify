import requests as requests


def pull_apiFachaDev(planes):
    import configparser
    main_config = configparser.ConfigParser()
    main_config.read('./configs/mainconf.ini')
    planeData = []
    token = None
    headers = None
    if main_config.has_option('API-FACHA-DEV', 'token'):
        token = main_config.get('API-FACHA-DEV', 'token') + "/api/aircraft/json/all"
        headers = {
            'Authorization': token,
            'Accept-Encoding': 'gzip'
        }
    failed = False
    icao_array = []
    for key in planes.keys():
        icao_array.append(key.lower())
    try:
        for icao in icao_array:
            response = requests.get(
                "https://api.facha.dev/v1/aircraft/live/icao/" + icao, headers=headers)
            if response.status_code == 200:
                if('error' not in response.json()):
                    planeData.append(response.json())
            else:
                # print(response.status_code)
                failed = True
        # print(planeData)
    except Exception as e:
            print ("FachaDev Error", e)
            failed = True
    return planeData, failed