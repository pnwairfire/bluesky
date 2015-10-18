"""bluesky.modules.dispersion

If running hysplit dispersion, you'll need to obtain hysplit from NOAA.It is
expected to reside in a directory in the search path. (This module prevents
configuring relative or absolute paths to hysplit, to eliminiate security
vulnerabilities when invoked by web service request.) To obtain hysplit, Go to
NOAA's [hysplit distribution page](http://ready.arl.noaa.gov/HYSPLIT.php).
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
    disperser.run(fires_manager)

    # TODO: add information to fires_manager indicating where to find the hysplit output
