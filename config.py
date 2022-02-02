import configparser

MAIN_CONFIG = configparser.ConfigParser()
MAIN_CONFIG.read("./configs/mainconf.ini")

PLANE_CONFIG = configparser.ConfigParser()
PLANE_CONFIG.read("./configs/plane1.ini")
