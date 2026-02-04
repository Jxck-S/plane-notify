"""src/aircraft_images.py: Utility functions for fetching aircraft photos and silhouettes."""

import json
import logging
from io import BytesIO
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

AIRCRAFT_SILS_DIR = "aircraft_sils"
TIMEOUT_SECS = 10
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


def get_planespotters_net_aircraft_photo(reg: str) -> dict | None:
    """
    Fetch aircraft photo information from Planespotters.net API.

    :param reg: Aircraft registration to look up.
    :return: Dictionary with image_url and credit, or None if not found.
    """
    try:
        logger.debug("Getting planespotters pic")
        headers = {"User-Agent": USER_AGENT}
        rsp = requests.get(
            f"https://api.planespotters.net/pub/photos/reg/{reg}",
            headers=headers,
            timeout=TIMEOUT_SECS,
        )

        if rsp.status_code != 200:
            logger.debug(
                "Planespotters API returned status code %s for %s", rsp.status_code, reg
            )
            return None

        if not rsp.text.strip():
            logger.debug("Planespotters API returned empty response for %s", reg)
            return None

        ps_reg_photo_info = json.loads(rsp.text)
        logger.debug(ps_reg_photo_info)
        if "photos" in ps_reg_photo_info and len(ps_reg_photo_info["photos"]) > 0:
            photo = ps_reg_photo_info["photos"][0]
            url = photo["thumbnail"]["src"]
            credit = photo["photographer"]
            return {
                "image_url": url,
                "credit": credit,
            }
        return None
    except json.JSONDecodeError as e:
        logger.exception(
            "Failed to parse JSON response from Planespotters API for %s: %s", reg, e
        )
        logger.debug("Response content: %s...", rsp.text[:200])  # Show first 200 chars
        return None
    except requests.exceptions.RequestException as e:
        logger.exception(
            "Request error when fetching from Planespotters API for %s: %s", reg, e
        )
        return None
    except Exception as e:
        logger.exception(
            "Unexpected error in get_planespotters_net_aircraft_photo for %s: %s",
            reg,
            e,
        )
        return None


def get_github_aircraft_photo(reg: str) -> dict | None:
    """
    Fetch aircraft photo information from a curated GitHub repository.

    :param reg: Aircraft registration to look up.
    :return: Dictionary with image_url and credit, or None if not found.
    """
    try:
        logger.debug("Getting Github List")
        rsp = requests.get(
            "https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/photo-list.json",
            timeout=TIMEOUT_SECS,
            headers={"User-Agent": USER_AGENT},
        )

        if rsp.status_code != 200:
            logger.debug(
                "GitHub photo list returned status code %s for %s", rsp.status_code, reg
            )
            return None

        if not rsp.text.strip():
            logger.debug("GitHub photo list returned empty response for %s", reg)
            return None

        photo_list = json.loads(rsp.text)
        if reg in photo_list:
            photo_name = photo_list[reg]["photo"]
            url = f"https://raw.githubusercontent.com/Jxck-S/aircraft-photos/main/images/{photo_name}"
            credit = photo_list[reg]["photographer"]
            return {"image_url": url, "credit": credit}
        return None
    except json.JSONDecodeError as e:
        logger.exception(
            "Failed to parse JSON response from GitHub photo list for %s: %s", reg, e
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.exception(
            "Request error when fetching GitHub photo list for %s: %s", reg, e
        )
        return None
    except Exception as e:
        logger.exception(
            "Unexpected error in get_github_aircraft_photo for %s: %s", reg, e
        )
        return None


def get_aircraft_sil(type_code: str) -> str | None:
    """
    Get the file path to an aircraft silhouette image.

    :param type_code: ICAO aircraft type code.
    :return: Path to the silhouette PNG file or None.
    """
    sil_path = str(Path(AIRCRAFT_SILS_DIR) / f"{type_code.upper()}.png")
    logger.debug(sil_path)
    if type_code and Path(sil_path).exists():
        logger.debug(sil_path)

        return sil_path
    return None


def get_aircraft_image_url(reg: str) -> str | None:
    """
    Attempt to find an aircraft image from multiple sources.

    :param reg: Aircraft registration.
    :return: Photo information dictionary or None.
    """
    photo = None
    if (photo := get_github_aircraft_photo(reg)) or (
        photo := get_planespotters_net_aircraft_photo(reg)
    ):
        pass

    return photo


def get_image_from_url(photo: str) -> str | None:
    """
    Download an aircraft image from a provided URL.

    :param photo: Dictionary containing 'image_url'.
    :return: BytesIO object containing image data or None.
    """
    try:
        url = photo["image_url"]
        response = requests.get(
            url, timeout=TIMEOUT_SECS, headers={"User-Agent": USER_AGENT}
        )

        if response.status_code == 200:
            # Read image data from the response content
            return BytesIO(response.content)
        logger.error("Failed to fetch image. Status code: %s", response.status_code)
        return None
    except requests.exceptions.RequestException as e:
        logger.exception("Request error when fetching image from %s: %s", url, e)
        return None
    except Exception as e:
        logger.exception("Unexpected error in get_image_from_url for %s: %s", url, e)
        return None
