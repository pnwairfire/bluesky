"""bluesky.modules.dispersion

If running hysplit dispersion, you'll need to obtain hysplit and various other
Executables. See the repo README.md for more information.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

from bluesky import datetimeutils
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

    # TDOO: rename 'start' and 'end' to indicate that 'end' is included
    #  e.g. if start=2014-05-29T22:00:00 and end=2014-05-30T00:00:00,
    #  dispersion run is for the three hours 5/29 22:00, 5/29 23:00, 5/30 00:00
    start = datetimeutils.parse_datetime(
        fires_manager.get_config_value('start'), 'start')
    end = datetimeutils.parse_datetime(
        fires_manager.get_config_value('end'), 'end')
    disperser.run(fires_manager, start, end)

    # TODO: add information to fires_manager indicating where to find the hysplit output
