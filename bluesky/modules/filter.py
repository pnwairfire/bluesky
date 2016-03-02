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
    logging.info("Running filter module")
    fires_manager.processed(__name__, __version__,
        num_fires_before=fires_manager.num_fires)
    fires_manager.filter_fires()
    fires_manager.processed(__name__, __version__,
        num_fires_after=fires_manager.num_fires)
