"""bluesky.web.lib.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser

__all__ = [
    'get_config_value'
]

def config_from_dict(config_dict):
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
    for s, s_dict in config_dict.items():
        config.add_section(s)
        for o, v in s_dict.items():
            config.set(s, o, v)
    return config

def get_config_value(config, section, key, default=None):
    if config:
        try:
            return config.get(section, key)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            pass
    return default
