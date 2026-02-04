"""
cnf_parser_ext.py: Direct Config Parser Extension

This module provides an extended `ConfigParserExt` class that inherits from `RawConfigParser`.
It adds helper methods to safely get values, booleans, and titles, handling missing sections or keys gracefully by returning fallbacks.
It also strips quotes from values automatically.
"""

import os
from configparser import RawConfigParser


class ConfigParserExt(RawConfigParser):
    def get(
        self, section, option, *, raw=False, vars_=None, fallback=None, **kwargs
    ) -> str | None:
        if not self.has_section(section):
            return fallback
        value = super().get(
            section, option, raw=raw, vars=vars_, fallback=fallback, **kwargs
        )
        return value.strip('"')

    def getboolean(
        self, section, option, *, raw=False, vars_=None, fallback=None, **kwargs
    ) -> bool | None:
        if not self.has_section(section) or not self.has_option(section, option):
            return fallback

        value = super().getboolean(
            section, option, raw=raw, vars=vars_, fallback=fallback, **kwargs
        )
        return value

    def get_title(self, section):
        if self.has_option(section, "TITLE"):
            modified_value = self.get(section, "TITLE")
            return modified_value
        else:
            return None

    def read(self, filenames, encoding=None):
        # Allow reading and storing the filename (assuming single file usage for Plane configs)
        if isinstance(filenames, str):
            self.filepath = os.path.basename(filenames)
        elif isinstance(filenames, list) and len(filenames) > 0:
            self.filepath = os.path.basename(filenames[0])
        else:
            self.filepath = None

        return super().read(filenames, encoding=encoding)
