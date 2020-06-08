"""bluesky.modules.growth"""

__author__ = "Tobias Schmidt"

__all__ = [
    'run'
]

__version__ = "1.0"

import logging
import os
import shutil

from bluesky import io
from bluesky import datautils
from bluesky.config import Config
from bluesky.persisters.persistence import Persistence

def run(fires_manager):
    """runs the growth module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """

    pers = Persistence()
    pers.run(fires_manager)

    datautils.summarize_all_levels(fires_manager, 'consumption')

    fires_manager.processed(__name__, __version__)
