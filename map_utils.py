import requests
import configparser

ZOOM = 9
URL = "https://maps.googleapis.com/maps/api/staticmap?"

CONFIG = configparser.ConfigParser()
CONFIG.read("./configs/mainconf.ini")

API_KEY = CONFIG.get("GOOGLE", "API_KEY")


def get_map(map_location, file_name):
    r = requests.get(
        f"{URL}center={map_location}&zoom={ZOOM}&size=800x800 &key={API_KEY}&sensor=false"
    )

    with open(file_name, "wb") as f:
        f.write(r.content)
