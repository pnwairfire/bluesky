"""bluesky.importutils"""

import importlib
import logging

from bluesky.exceptions import BlueSkyConfigurationError

def import_class(module_name, klass_name):
    module = import_module(module_name)

    logging.debug("Loading class %s", klass_name)
    try:
        klass = getattr(module, klass_name)
    except:
        # TODO: use more appropriate exception class
        raise BlueSkyConfigurationError("{} does not define class {}".format(
            module_name, klass_name))

    return module, klass

def import_module(module_name):
    logging.debug("Importing %s", module_name)
    try:
        return importlib.import_module(module_name)
    except ImportError:
        raise BlueSkyConfigurationError(
            "Invalid module: '{}'".format(module_name))
