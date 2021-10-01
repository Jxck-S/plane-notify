import json
import os
folder = os.getcwd() + "/dependencies"
def get_aircraft_reg_by_icao(icao):
    with open(folder + '/aircrafts.json') as aircrafts_json:
        aircraft = json.load(aircrafts_json)
        try:
            reg = aircraft[icao.upper()][0]
        except KeyError:
            reg = None
        return reg
def get_type_code_by_icao(icao):
    with open(folder + '/aircrafts.json') as aircrafts_json:
        aircraft = json.load(aircrafts_json)
        try:
            type_code = aircraft[icao.upper()][1]
        except KeyError:
            type_code = None
        return type_code

def get_type_desc(t):
    with open(folder + '/types.json') as types_json:
        types = json.load(types_json)
        return types[t.upper()]

def get_db_ver():
    with open(folder + '/dbversion.json') as dbver_json:
        dbver = json.load(dbver_json)
    return dbver["version"]
def test():
    print(get_aircraft_reg_by_icao("A835AF"))
    print(get_type_code_by_icao("A835AF"))
    print(get_type_desc("GLF6"))
    print(get_db_ver())
#test()