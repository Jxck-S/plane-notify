"""
cnf_parser_ext.py: Direct Config Parser Extension

This module provides an extended `ConfigParserExt` class that inherits from `RawConfigParser`.
It adds helper methods to safely get values, booleans, and titles, handling missing sections or keys gracefully by returning fallbacks.
It also strips quotes from values automatically.
"""
from configparser import RawConfigParser

class ConfigParserExt(RawConfigParser):
    def get(self, section, option, *, raw=False, vars=None, fallback=None):
        if not self.has_section(section):
            return fallback
        value = super().get(section, option, raw=raw, vars=vars, fallback=fallback)
        return value.strip('"')
    def getboolean(self, section, option, *, raw=False, vars=None, fallback=None):
        if not self.has_section(section) or not self.has_option(section, option):
            return fallback
        
        value = super().getboolean(section, option, raw=raw, vars=vars, fallback=fallback)
        return value

    def get_title(self, section):
        if self.has_option(section, 'TITLE'):
            modified_value = self.get(section, 'TITLE')
            return modified_value
        else:
            return None

