#Flight Logging Functions
def add_flight(cursor, reg, icao, callsign, origin, takeoff_confirmed, takeoff_time):
    '''Adds a flight record to the flight table, meant for use on takeoff'''
    sql = """INSERT INTO "plane-notify".flights (reg, icao, origin, callsign, takeoff_confirmed, takeoff_time) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id"""
    print(sql)
    cursor.execute(sql, (reg, icao, origin, callsign, takeoff_confirmed, takeoff_time))
    db_flight_id = cursor.fetchone()['id']
    print(f"Added flight to db with id: {db_flight_id}")
    return db_flight_id

def update_flight(cursor, db_flight_id, destination, landing_confirmed, landing_time):
    '''Updates a flight record in the flight table, meant for use on landing'''
    sql = """UPDATE "plane-notify".flights
        SET destination = %s,
            landing_confirmed = %s,
            landing_time = %s
        WHERE id = %s"""
    print(f"Updated flight with id: {db_flight_id}")
    cursor.execute(sql, (destination, landing_confirmed, landing_time, db_flight_id))

#Aircraft Info Functions
def get_aircraft_reg_by_icao(icao, cursor):
    '''Retrive an aircrafts reg/tail number based on icao/hex'''
    sql = "SELECT reg from deps.aircraft_v WHERE icao = %s"
    cursor.execute(sql, (icao.lower(),))
    if cursor.rowcount > 0:
        reg = cursor.fetchone()['reg']
    else:
        reg = None
    
    return reg

def get_type_code_by_icao(icao, cursor):
    '''Retrive an aircrafts icao type code based on icao/hex'''
    sql = "SELECT icaotype from deps.aircraft_v WHERE icao = %s"
    cursor.execute(sql, (icao.lower(),))
    if cursor.rowcount > 0:
        type_code = cursor.fetchone()['icaotype']
    else:
        type_code = None
    return type_code
