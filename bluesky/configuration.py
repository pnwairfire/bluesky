"""bluesky.web.lib.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser

from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'config_parser_to_dict',
    'get_config_value'
]

##
## Converting from ConfigParser objects
##

def config_parser_to_dict(config):
    d = {}
    if config:
        return {s:{k:v for k,v in config.items(s)} for s in config.sections()}
    return d

##
## Utility mehtods
##

def get_config_value(config, *keys, **kwargs):
    """Returns value from arbitrary nesting in config dict

    Recognized kwargs:
     - default -- if not specified, None is used as the default
    """
    default = kwargs.get('default', None)
    if config and isinstance(config, dict) and keys:
        if len(keys) == 1:
            return config.get(keys[0], default)
        elif keys[0] in config:
            return get_config_value(config[keys[0]], *keys[1:], **kwargs)
    return default

INVALID_CONFIG_ERR_MSG = "Expecting dict to hold config"
MISSING_KEYS_ERR_MSG = "Specify config keys to set value"

def set_config_value(config, value, *keys):
    if not isinstance(config, dict):
        raise BlueSkyConfigurationError(INVALID_CONFIG_ERR_MSG)
    if not keys:
        raise BlueSkyConfigurationError(MISSING_KEYS_ERR_MSG)

    # TODO: prevent overriding of existing value ?
    if len(keys) == 1:
        config[keys[0]] = value
    else:
        if not isinstance(config.get(keys[0]), dict):
            config[keys[0]] = dict()
        set_config_value(config[keys[0]], value, *keys[1:])
