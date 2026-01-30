from enum import Enum

class Flags(Enum):
    LADD = "LADD"
    PIA = "PIA"
    MILITARY = "Military"
    INTRESTING = "Interesting"
    HEAVY = "Heavy"
    SUPER = "Super"

class ImageTypes(str, Enum):
    LANDED = "landed"
    TAKEOFF = "takeoff"
    EMERGENCY = "emergency"
    APPROACH = "approach"
    CIRCLING = "circling"
