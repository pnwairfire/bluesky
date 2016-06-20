"""bluesky.configuration

TODO: create ConfigDict class with method 'merge' (which, as the name
  implies, merges another config dict in place)
"""

__author__ = "Joel Dubowy"

import argparse
import configparser
import json
import os
import re

from pyairfire.scripting.args import (
    ConfigOptionAction,
    BooleanConfigOptionAction,
    IntegerConfigOptionAction,
    FloatConfigOptionAction,
    JSONConfigOptionAction,
    ConfigFileAction
)

from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'config_parser_to_dict',
    'get_config_value',
    'set_config_value',
    'merge_configs',
    'ConfigOptionAction',
    'BooleanConfigOptionAction',
    'IntegerConfigOptionAction',
    'FloatConfigOptionAction',
    'JSONConfigOptionAction',
    'ConfigFileAction'
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

NO_KEYS_ERR_MSG = "No config key(s) specified"
def get_config_value(config, *keys, **kwargs):
    """Returns value from arbitrary nesting in config dict

    Recognized kwargs:
     - default -- if not specified, None is used as the default
    """
    if not keys:
        raise BlueSkyConfigurationError(NO_KEYS_ERR_MSG)

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

CONFIG_CONFLICT = "Conflicting config dicts. Can't be merged."

def merge_configs(config, to_be_merged_config):
    if not isinstance(config, dict) or not isinstance(to_be_merged_config, dict):
        raise BlueSkyConfigurationError(INVALID_CONFIG_ERR_MSG)

    # Merge in place
    for k, v in to_be_merged_config.items():
        if k not in config or (
                not isinstance(config[k], dict) and not isinstance(v, dict)):
            config[k] = v
        elif isinstance(config[k], dict) and isinstance(v, dict):
            merge_configs(config[k], v)
        else:
            raise BlueSkyConfigurationError(CONFIG_CONFLICT)

    # return reference to config, even though it was merged in place
    return config

##
## Config dict immutability
##

# TODO: move ImmutableConfigDict to pyairfire?

class ImmutableConfigDict(dict):
    # from https://www.python.org/dev/peps/pep-0351/

    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kws):
        raise TypeError('object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear       = _immutable
    update      = _immutable
    setdefault  = _immutable
    pop         = _immutable
    popitem     = _immutable


