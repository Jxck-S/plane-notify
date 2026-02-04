import db


def get_closest_airport(latitude, longitude, allowed_types):
    """
    Find the closest airport to a given coordinate within allowed types.

    Uses PostGIS ST_Distance to calculate the nearest airport of the specified
    types (e.g., 'large_airport', 'medium_airport') and returns its details.
    """
    if not db.tracking_cursor:
        return None
    allowed_types_list = [t.strip() for t in allowed_types.strip("[]").split(",")]
    sql = """
        SELECT oaa.ident, oaa.type, oaa.name, oaa.lat, oaa.lon,
               oaa.elev as elevation_ft, oaa.continent, oaa.iso_country,
               oaa.iso_region, oaa.municipality, oaa.icao_code,
               oaa.iata_code, oaa.local_code, oar.name as region,
               oac.name as country,
               ST_Distance(
                   ST_MakePoint(%s, %s)::geography,
                   ST_MakePoint(oaa.lon, oaa.lat)
               ) / 1609 as distance_mi
        FROM deps.our_airports_airports oaa,
             deps.our_airports_regions oar,
             deps.our_airports_countries oac
        WHERE oaa.geog <> ST_MakePoint(%s, %s)
          AND type = ANY(%s)
          AND oaa.iso_region = oar.code AND oaa.iso_country = oac.code
        ORDER BY distance_mi
        LIMIT 1;
    """
    vals = [longitude, latitude, longitude, latitude, allowed_types_list]
    db.tracking_cursor.execute(sql, vals)
    return dict(db.tracking_cursor.fetchone())


def get_airport_by_icao(icao):
    """
    Retrieve airport information based on its ICAO code.

    Queries the database for an airport matching the provided ICAO/GPS code
    and returns a dictionary of its attributes.
    """
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
