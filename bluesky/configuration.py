"""bluesky.configuration

TODO: create ConfigDict class with method 'merge' (which, as the name
  implies, merges another config dict in place)
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import argparse
import ConfigParser
import json
import os
import re

from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'config_parser_to_dict',
    'get_config_value',
    'set_config_value',
    'merge_configs',
    'ConfigOptionAction'
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
## Parsing config options from the command line
##

# TODO: move Config*Action classes to pyairfire ?

class ConfigOptionAction(argparse.Action):

    EXTRACTER = re.compile('^([^=]+)=([^=]+)$')

    def __call__(self, parser, namespace, value, option_string=None):
        """Set individual config option in config dict

        Note: Expects value to be of the format 'section.*.key=value', with
        any section nesting depth.

        TODO: come up with way to specify numeric and boolean values
          (maybe have separate option, e.g. '--int-config-option'; would
           need to do something like subclass ConfigOptionAction and
           have hook for setting value so that subclasses could used
           that hook to cast to int)
        """
        m = self.EXTRACTER.search(value.strip())
        if not m:
            msg = ("Invalid value '{}' for option '{}' - value must be of the "
                "form 'section.*.key=value'".format(value, opt))
            raise argparse.ArgumentTypeError(msg)

        config_dict = getattr(namespace, self.dest)
        if not config_dict:
            config_dict = dict()
            setattr(namespace, self.dest, config_dict)

        set_config_value(config_dict, m.group(2), *m.group(1).split('.'))

class ConfigFileAction(argparse.Action):
    def __call__(self, parser, namespace, value, option_string=None):
        """Load config settings from json file
        """
        filename = os.path.abspath(value.strip())
        if not os.path.isfile(filename):
            raise argparse.ArgumentTypeError(
                "File {} does not exist".format(filename))

        with open(filename) as f:
            try:
                config_dict = json.loads(f.read())
            except ValueError:
                raise argparse.ArgumentTypeError("File {} contains "
                    "invalid config JSON data".format(filename))

        if 'config' not in config_dict:
            raise argparse.ArgumentTypeError("Config file must contain top "
                "level 'config' key")
        config_dict = config_dict['config']

        existing_config_dict = getattr(namespace, self.dest)
        if not existing_config_dict:
            # first file loaded
            setattr(namespace, self.dest, config_dict)
        else:
            # subsequent file loaded
            merge_configs(existing_config_dict, config_dict)
