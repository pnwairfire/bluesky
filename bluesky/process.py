"""bluesky.process

# TODO: rename this module and move it?
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import importlib
import logging
import traceback

from bluesky.exceptions import BlueSkyImportError, BlueSkyModuleError

__all__ = [
    "run_modules"
]

##
## Public functions
##

def run_modules(module_names, fires_manager, config):
    """Imports modules and runs them.
    """
    modules = []
    for m in module_names:
        try:
            modules.append(importlib.import_module('bluesky.modules.%s' % (m)))
        except ImportError, e:
            raise BlueSkyImportError("Invalid module '{}'".format(m))

    fires_manager.summary = fires_manager.summary or {}
    fires_manager.processing = fires_manager.processing or []

    try:
        for module in modules:
            # TDOO: catch any exception raised by a module and dumps
            # whatever is the current state of fires (or state of fires prior
            # to calling hte module) ?
            # 'run' modifies fires in place
            module.run(fires_manager, config)
    except Exception, e:
        # when there's an error running modules, don't bail; raise
        # BlueSkyModuleError so that the calling code can decide what to do
        # (which, in the case of bsp and bsp-web, is to dump the data as is)
        logging.error(e)
        tb = traceback.format_exc()
        logging.debug(tb)
        fires_manager.error = {
            "message": str(e),
            "traceback": str(tb)
        }
        raise BlueSkyModuleError(e)
