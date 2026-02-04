"""cnf_parser_ext.py: Direct Config Parser Extension.

This module provides an extended `ConfigParserExt` class that inherits from `RawConfigParser`.
It adds helper methods to safely get values, booleans, and titles, handling missing sections or keys gracefully by returning fallbacks.
It also strips quotes from values automatically.
"""

import os
from configparser import RawConfigParser


class ConfigParserExt(RawConfigParser):
    """Configuration parser with quote stripping and safety fallbacks."""

    def get(
        self, section, option, *, raw=False, vars_=None, fallback=None, **kwargs
    ) -> str | None:
        """Safely retrieve a string value from the configuration.

        :param section: Section name.
        :param option: Option name.
        :param raw: Whether to return raw values.
        :param vars_: Variables for interpolation.
        :param fallback: Value to return if section/option is missing.
        :return: Stripped string value or fallback.
        """
        if not self.has_section(section):
            return fallback
        value = super().get(
            section, option, raw=raw, vars=vars_, fallback=fallback, **kwargs
        )
        return value.strip('"')

    def getboolean(
        self, section, option, *, raw=False, vars_=None, fallback=None, **kwargs
    ) -> bool | None:
        """Safely retrieve a boolean value from the configuration.

        :param section: Section name.
        :param option: Option name.
        :param raw: Whether to return raw values.
        :param vars_: Variables for interpolation.
        :param fallback: Value to return if section/option is missing.
        :return: Boolean value or fallback.
        """
        if not self.has_section(section) or not self.has_option(section, option):
            return fallback

        return super().getboolean(
            section, option, raw=raw, vars=vars_, fallback=fallback, **kwargs
        )

    def get_title(self, section):
        """Retrieve the 'TITLE' option for a given section.

        :param section: Section name.
        :return: The title string or None.
        """
        if self.has_option(section, "TITLE"):
            return self.get(section, "TITLE")
        return None

    def read(self, filenames, encoding=None):
        """Read and parse a list of filenames, storing the first filename as filepath.

        :param filenames: Filename or list of filenames.
        :param encoding: File encoding.
        :return: List of successfully read files.
        """
        # Allow reading and storing the filename (assuming single file usage for Plane configs)
        if isinstance(filenames, str):
            self.filepath = os.path.basename(filenames)
        elif isinstance(filenames, list) and len(filenames) > 0:
            self.filepath = os.path.basename(filenames[0])
        else:
            self.filepath = None

        return super().read(filenames, encoding=encoding)
