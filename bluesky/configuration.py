"""bluesky.web.lib.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser

__all__ = [
    'get_config_value'
]

##
## Converting between dict and ConfigParser objects
##

def config_parser_from_dict(config_dict):
    """Converts a dict of configuration data into a configparser object

    args:
     - config_dict -- dict of configuration data

    The config dict is of the form:

        {
            "section": {
                "option": "value"
                /* ... */
            }
            /* ... */
        }

    ex.

    """
    config = ConfigParser.ConfigParser()
    if config_dict:
        if not isinstance(config_dict, dict):
            raise ValueError("Config must be specified as a dict of nested section dicts")
        for s, s_dict in config_dict.items():
            if not isinstance(s_dict, dict):
                raise ValueError("Config sections must be specified as a dicts")
            config.add_section(s)
            for o, v in s_dict.items():
                config.set(s, o, v)
    return config

def config_parser_to_dict(config):
    d = {}
    if config:
        return {s:{k:v for k,v in config.items(s)} for s in config.sections()}
    return d

##
## Utility mehtods
##

def get_config_value(config, section, key, default=None):
    if config:
        try:
            return config.get(section, key)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            pass
    return default
