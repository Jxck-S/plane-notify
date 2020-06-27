def pullplane(TRACK_PLANE):
    from opensky_api import OpenSkyApi
    opens_api = OpenSkyApi("<openskyusername>", "<openskypass>")
    planeData = opens_api.get_states(time_secs=0, icao24=TRACK_PLANE.lower())
    return planeData