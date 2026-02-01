from enum import Enum, StrEnum


class Flags(Enum):
    LADD = "LADD"
    PIA = "PIA"
    MILITARY = "Military"
    INTRESTING = "Interesting"
    HEAVY = "Heavy"
    SUPER = "Super"


class ImageTypes(StrEnum):
    LANDED = "landed"
    TAKEOFF = "takeoff"
    EMERGENCY = "emergency"
    APPROACH = "approach"
    CIRCLING = "circling"
    RA = "ra"


class NavModes(Enum):
    TCAS = ("tcas", "TCAS")
    LNAV = ("lnav", "LNAV")
    VNAV = ("vnav", "VNAV")
    ALTHOLD = ("alt_hold", "Altitude hold")
    APPROACH = ("approach", "Approach")

    def __str__(self):
        return self.value[1]


# Create a lookup dictionary for O(1) access
NAV_MODE_LOOKUP = {nav.value[0]: nav for nav in NavModes}


def normalize_nav_modes(modes: list) -> list:
    normalized_modes = []
    for mode in modes:
        # Direct lookup using the lowercased input string
        normalized_mode = NAV_MODE_LOOKUP.get(mode.lower())

        if normalized_mode:
            normalized_modes.append(normalized_mode)

    return normalized_modes
