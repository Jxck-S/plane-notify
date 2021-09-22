def calculate_from_bearing(frm, to):
    """Calculate inital bearing from one coordinate to next (two tuples of coordinates(lat/lng) in degrees in, returns single bearing)"""
    #https://gis.stackexchange.com/questions/228656/finding-compass-direction-between-two-distant-gps-points
    from math import atan2, cos, radians, sin, degrees
    frm = (radians(frm[0]), radians(frm[1]))
    to = (radians(to[0]), radians(to[1]))
    y = sin(to[1]- frm[1]) * cos(to[0])
    x = cos(frm[0]) * sin(to[0]) - sin(frm[0]) * cos(to[0]) * cos(to[1]-frm[1])
    from_bearing = degrees(atan2(y, x))
    if from_bearing < 0:
        from_bearing += 360
    return from_bearing
def calculate_cardinal(d):
    """Finds cardinal direction from bearing degree"""
    dirs = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    ix = int(round(d / (360. / len(dirs))))
    card = dirs[ix % len(dirs)]
    print(card)
    return card
def calculate_deg_change(new_heading, original_heading):
    """Calculates change between two headings, returns negative degree if change is left, positive if right"""
    normal = abs(original_heading-new_heading)
    across_inital = 360 - abs(original_heading-new_heading)
    if across_inital < normal:
        direction = "left" if original_heading < new_heading else "right"
        track_change = across_inital
    else:
        direction = "right" if original_heading < new_heading else "left"
        track_change = normal
    if direction == "left":
        track_change *= -1
    print(f"Track change of {track_change}° which is {direction}")
    return track_change

