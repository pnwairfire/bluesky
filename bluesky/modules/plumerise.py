"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

__all__ = [
    'run'
]

__version__ = "0.1.0"


def run(fires_manager, config=None):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    raise NotImplementedError("plumerise not yet implemented")
