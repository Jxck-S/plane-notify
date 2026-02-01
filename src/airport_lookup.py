import db


def getClosestAirport(latitude, longitude, allowed_types):
    if not db.tracking_cursor:
        return None
    allowed_types = allowed_types.strip("[]").split(", ")
    allowed_types_ses = ("%s, " * len(allowed_types))[:-2]
    sql = f"""SELECT oaa.ident, oaa.type, oaa.name, oaa.lat, oaa.lon, oaa.elev as elevation_ft, oaa.continent, oaa.iso_country, oaa.iso_region, oaa.municipality, oaa.icao_code, oaa.iata_code, oaa.local_code,
	oar.name as region,
    oac.name as country,
	ST_Distance(ST_MakePoint(%s, %s)::geography, ST_MakePoint(oaa.lon,oaa.lat)) / 1609 as distance_mi
	FROM deps.our_airports_airports oaa, deps.our_airports_regions oar, deps.our_airports_countries oac
	WHERE oaa.geog <> ST_MakePoint(%s, %s) AND type in ({allowed_types_ses}) AND oaa.iso_region = oar.code AND oaa.iso_country = oac.code
	ORDER BY distance_mi
	LIMIT 1;
	"""
    vals = [longitude, latitude, longitude, latitude]
    vals.extend(allowed_types)
    db.tracking_cursor.execute(sql, vals)
    closest_airport_dict = dict(db.tracking_cursor.fetchone())
    return closest_airport_dict


def get_airport_by_icao(icao):
    if not db.tracking_cursor:
        return None
    sql = """SELECT oaa.ident, oaa.type, oaa.name, oaa.lat, oaa.lon, oaa.elev, oaa.continent, oaa.iso_country, oaa.iso_region, oaa.municipality, oaa.icao_code, oaa.iata_code, oaa.local_code,
	oar.name as region,
    oac.name as country
	FROM deps.our_airports_airports oaa, deps.our_airports_regions oar, deps.our_airports_countries oac
	WHERE oaa.gps_code = %s AND oaa.iso_region = oar.code AND oaa.iso_country = oac.code
	LIMIT 1;
	"""
    db.tracking_cursor.execute(sql, [icao])
    if db.tracking_cursor.rowcount > 0:
        airport_dict = dict(db.tracking_cursor.fetchone())
    else:
        airport_dict = None
    return airport_dict
