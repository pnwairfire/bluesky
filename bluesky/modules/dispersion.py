"""bluesky.modules.dispersion

If running hysplit dispersion, you'll need to obtain hysplit and various other
Executables. See the repo README.md for more information.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

from bluesky.hysplit import hysplit

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager, config=None):
    """Runs dispersion module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    model = fires_manager.get_config_value('dispersion', 'model',
        default='hysplit').lower()

    # TODO: support VSMOKE as well
    if model == 'hysplit':
        hysplit_config = fires_manager.get_config_value('dispersion', 'hysplit',
            default={})
        disperser = hysplit.HYSPLITDispersion(**hysplit_config)
    else:
        raise BlueSkyConfigurationError(
            "Invalid dispersion model: '{}'".format(model))


    # TODO: pass gathered data into wrapper
    disperser.run(fires_manager, fires_manager.get_config_value('start'),
        fires_manager.get_config_value('end'))

    # TODO: add information to fires_manager indicating where to find the hysplit output
