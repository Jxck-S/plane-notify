import logging

import psycopg2
import psycopg2.extras

tracking_db = None
tracking_cursor = None
tracking_config = None

logger = logging.getLogger(__name__)


def init_db(config):
    global tracking_db, tracking_cursor, tracking_config
    tracking_config = config
    if config.has_section("DB"):
        flight_logging_status = (
            "Enabled" if config.getboolean("DB", "FLIGHT_LOGGING") else "Disabled"
        )
        tracking_db = psycopg2.connect(
            host=config.get("DB", "HOST"),
            port=config.getint("DB", "PORT"),
            user=config.get("DB", "USERNAME"),
            password=config.get("DB", "PASSWORD"),
            database=config.get("DB", "DATABASE"),
            options="-c application_name=plane-notify",
        )
        logger.info(
            f"""Connected to db at {config.get("DB", "HOST")}:{config.getint("DB", "PORT")} | Flight Logging: {flight_logging_status}"""
        )
        tracking_cursor = tracking_db.cursor(
            cursor_factory=psycopg2.extras.RealDictCursor
        )
    else:
        logger.info("DB section missing in config, cannot connect.")


# Flight Logging Functions
def add_flight(reg, icao, callsign, origin, takeoff_confirmed, takeoff_time):
    """Adds a flight record to the flight table, meant for use on takeoff"""

    if not tracking_cursor:
        return None
    if tracking_config.getboolean("DB", "FLIGHT_LOGGING") is False:
        return None
    sql = """INSERT INTO "plane-notify".flights (reg, icao, origin, callsign, takeoff_confirmed, takeoff_time) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"""
    tracking_cursor.execute(
        sql, (reg, icao, origin, callsign, takeoff_confirmed, takeoff_time)
    )
    db_flight_id = tracking_cursor.fetchone()["id"]
    tracking_db.commit()
    logger.info(f"Added flight to db with id: {db_flight_id}")
    return db_flight_id


def update_flight(db_flight_id, destination, landing_confirmed, landing_time):
    """Updates a flight record in the flight table, meant for use on landing"""

    if not tracking_cursor:
        return
    if tracking_config.getboolean("DB", "FLIGHT_LOGGING") is False:
        return
    sql = """UPDATE "plane-notify".flights
        SET destination = %s,
            landing_confirmed = %s,
            landing_time = %s
        WHERE id = %s"""
    logger.info(f"Updated flight with id: {db_flight_id}")
    tracking_cursor.execute(
        sql, (destination, landing_confirmed, landing_time, db_flight_id)
    )
    tracking_db.commit()


# Aircraft Info Functions
def get_aircraft_reg_by_icao(icao):
    """Retrive an aircrafts reg/tail number based on icao/hex"""
    if not tracking_cursor:
        return None
    sql = "SELECT reg from deps.aircraft_v WHERE icao = %s"
    tracking_cursor.execute(sql, (icao.lower(),))
    if tracking_cursor.rowcount > 0:
        reg = tracking_cursor.fetchone()["reg"]
    else:
        reg = None

    return reg


def get_type_code_by_icao(icao):
    """Retrive an aircrafts icao type code based on icao/hex"""
    if not tracking_cursor:
        return None
    sql = "SELECT icaotype from deps.aircraft_v WHERE icao = %s"
    tracking_cursor.execute(sql, (icao.lower(),))
    if tracking_cursor.rowcount > 0:
        type_code = tracking_cursor.fetchone()["icaotype"]
    else:
        type_code = None
    return type_code
