import re
import configparser
def set_dyn_title(title, *aircraft_info):
    if not title:
        return ""
    elif title.upper() in ['DYNAMIC', 'CALLSIGN']:
        for info in aircraft_info:
            if info:
                return info
        return None
    else:
        return title
    
def clean_stack_trace(stack_trace):
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

def apply_prefix(prefix, message):
    if prefix:
        return f"{prefix} {message}"
    else:
        return message


def extract_operator_icao(callsign: str) -> str | None:
    """
    Extracts the ICAO operator code from a callsign.

    Parameters:
    callsign (str): The callsign from which to extract the ICAO operator code.

    Returns:
    str | None: The extracted ICAO operator code if the callsign is valid, otherwise None.
    """
    if callsign and len(callsign) > 3 and callsign[0:3].isalpha() and callsign[3].isdigit():
        return callsign[0:3]
    else:
        return None
