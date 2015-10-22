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
    processed_kwargs = {}
    try:
        # TODO: support VSMOKE as well
        if model == 'hysplit':
            hysplit_config = fires_manager.get_config_value('dispersion', 'hysplit',
                default={})
            disperser = hysplit.HYSPLITDispersion(**hysplit_config)
            processed_kwargs.update(hysplit_version=hysplit.__version__)
        else:
            raise BlueSkyConfigurationError(
                "Invalid dispersion model: '{}'".format(model))

        start_str = fires_manager.get_config_value('dispersion', 'start')
        num_hours = fires_manager.get_config_value('dispersion', 'num_hours')
        if not start_str or not num_hours:
            raise ValueError(
                "Config settings 'start' and 'num_hours' required for computing dispersion")
        start = datetimeutils.parse_datetime(start_str, 'start')
        # further validation of start and num_hours done in HYSPLITDispersion.run
        disperser.run(fires_manager.fires, start, num_hours)
        # TODO: add information about fires to processed_kwargs
    finally:
        fires_manager.processed(__name__, __version__, model=model,
            **processed_kwargs)

    # TODO: add information to fires_manager indicating where to find the hysplit output
