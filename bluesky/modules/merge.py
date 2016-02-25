"""bluesky.modules.merge"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import logging

__all__ = [
    'run'
]

__version__ = "0.1.0"


def run(fires_manager):
    """Merges fires with the same id

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running merge module")
    fires_manager.processed(__name__, __version__)
    fires_manager.merge_fires()
