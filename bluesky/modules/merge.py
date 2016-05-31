"""bluesky.modules.merge"""

__author__ = "Joel Dubowy"

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
    processed_kwargs = {
        "num_fires_before": fires_manager.num_fires
    }
    try:
        fires_manager.merge_fires()
        processed_kwargs.update(num_fires_after=fires_manager.num_fires)
    finally:
        fires_manager.processed(__name__, __version__,**processed_kwargs)
