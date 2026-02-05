"""utils.py: General utility functions."""

from __future__ import annotations

import contextlib
from pathlib import Path


def cleanup_images(path: str | None) -> None:
    """Delete temporary image files with given path prefix and common extensions."""
    if path:
        for ext in [".png", ".jpg"]:
            with contextlib.suppress(FileNotFoundError):
                Path(path + ext).unlink()


def set_dyn_title(title: str | None, *aircraft_info: str | None) -> str | None:
    """Determine dynamic title based on title value and aircraft info."""
    if not title:
        return ""
    if title.upper() in ["DYNAMIC", "CALLSIGN"]:
        for info in aircraft_info:
            if info:
                return info
        return None
    return title


def clean_stack_trace(stack_trace: str) -> str:
    """Clean stack trace by removing unknown entries."""
    cleaned_trace = []
    lines = stack_trace.splitlines()
    found_bad = False
    for line in lines:
        # Remove lines containing the word "unknown", useful for Selenium unknown stack traces
        if "<unknown>" not in line:
            # Optionally, you can remove other unwanted patterns using regular expressions
            # For example: line = re.sub(r'unwanted_pattern', '', line)
            cleaned_trace.append(line)
        else:
            found_bad = True
    cleaned_stack_trace = "\n".join(cleaned_trace)
    if found_bad:
        cleaned_stack_trace += "\n --Redacted Unknown Stack Traces--"
    return cleaned_stack_trace


def apply_prefix(prefix: str | None, message: str) -> str:
    """Prepend prefix to message if prefix exists."""
    if prefix:
        return f"{prefix} {message}"
    return message


def extract_operator_icao(callsign: str) -> str | None:
    """
    Extract the ICAO operator code from a callsign.

    :param callsign: The callsign from which to extract the ICAO operator code.
    :return: The extracted ICAO operator code if valid, otherwise None.
    """
    if (
        callsign
        and len(callsign) > 3
        and callsign[0:3].isalpha()
        and callsign[3].isdigit()
    ):
        return callsign[0:3]
    return None
