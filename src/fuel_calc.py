import logging

import db

logger = logging.getLogger(__name__)


def get_avg_fuel_price():
    if not db.tracking_cursor:
        return None
    sql = """SELECT cost::numeric::float FROM "plane-notify".fuel"""
    db.tracking_cursor.execute(sql)
    if db.tracking_cursor.rowcount > 0:
        cost = db.tracking_cursor.fetchone()["cost"]
        logger.debug("AVG fuel cost per gallong is $%s", cost)
        return cost
    return None


def fuel_calculation(aircraft_icao_type, minutes):
    """Calculates fuel usage, price, c02 output of a flight depending on aircraft type and flight length."""
    if not db.tracking_cursor:
        return None
    sql = """SELECT galph FROM "plane-notify".icao_type_info WHERE icao_code = %s """
    db.tracking_cursor.execute(sql, (aircraft_icao_type,))
    if db.tracking_cursor.rowcount > 0:
        fuel_flight_info = {}
        galph = db.tracking_cursor.fetchone()["galph"]
        avg_fuel_price_per_gallon = get_avg_fuel_price()
        fuel_used_gal = galph * (minutes / 60)
        if avg_fuel_price_per_gallon:
            fuel_flight_info["fuel_price"] = round(
                fuel_used_gal * avg_fuel_price_per_gallon
            )
        fuel_used_kg = fuel_used_gal * 3.04
        c02_tons = (fuel_used_kg * 3.15) / 907.185
        fuel_flight_info["fuel_used_kg"] = round(fuel_used_kg)
        fuel_flight_info["fuel_used_gal"] = round(fuel_used_gal)
        fuel_flight_info["fuel_used_lters"] = round(fuel_used_gal * 3.78541)
        fuel_flight_info["fuel_used_lbs"] = round(fuel_used_kg * 2.20462)
        fuel_flight_info["c02_tons"] = (
            round(c02_tons) if c02_tons > 1 else round(c02_tons, 4)
        )
        logger.debug("Fuel info %s", fuel_flight_info)
        return fuel_flight_info
    logger.warning("Can't calculate fuel info unknown aircraft ICAO type")
    return None


def fuel_message(fuel_info):
    have_cost = False
    if "fuel_price" in fuel_info:
        cost = "{:,}".format(fuel_info["fuel_price"])
        have_cost = True
    gallons = "{:,}".format(fuel_info["fuel_used_gal"])
    lters = "{:,}".format(fuel_info["fuel_used_lters"])
    lbs = "{:,}".format(fuel_info["fuel_used_lbs"])
    kgs = "{:,}".format(fuel_info["fuel_used_kg"])
    fuel_message = f"""\n~ {gallons} gallons ({lters} liters). \n~ {lbs} lbs ({kgs} kg) of jet fuel used. \n{(f"~ ${cost} cost of fuel." if have_cost else "Cost of fuel unavailable")} \n~ {fuel_info["c02_tons"]} tons of CO2 emissions."""
    logger.info(fuel_message)
    return fuel_message
