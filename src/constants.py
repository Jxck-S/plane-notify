"""src/constants.py: Global enumeration and constant definitions for the project."""

from enum import Enum, StrEnum


class Flags(Enum):
    """Enumeration for database aircraft flags."""

    LADD = "LADD"
    PIA = "PIA"
    MILITARY = "Military"
    INTRESTING = "Interesting"
    HEAVY = "Heavy"
    SUPER = "Super"


class ImageTypes(StrEnum):
    """Enumeration for different types of generated images."""

    LANDED = "landed"
    TAKEOFF = "takeoff"
    EMERGENCY = "emergency"
    APPROACH = "approach"
    CIRCLING = "circling"
    RA = "ra"


class NavModes(Enum):
    """Enumeration for aircraft navigation modes."""

    TCAS = ("tcas", "TCAS")
    LNAV = ("lnav", "LNAV")
    VNAV = ("vnav", "VNAV")
    ALTHOLD = ("alt_hold", "Altitude hold")
    APPROACH = ("approach", "Approach")

    def __str__(self) -> str:
        """Return the human-readable name of the navigation mode."""
        return self.value[1]


# Create a lookup dictionary for O(1) access
NAV_MODE_LOOKUP = {nav.value[0]: nav for nav in NavModes}


def normalize_nav_modes(modes: list[str]) -> list[NavModes]:
    """
    Convert a list of raw navigation mode strings into NavModes enum members.

    :param modes: List of mode strings from the data source.
    :return: List of NavModes enum members.
    """
    normalized_modes = []
    for mode in modes:
        # Direct lookup using the lowercased input string
        normalized_mode = NAV_MODE_LOOKUP.get(mode.lower())

        if normalized_mode:
            normalized_modes.append(normalized_mode)

    return normalized_modes
