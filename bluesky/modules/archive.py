"""bluesky.modules.export"""

__author__ = "Joel Dubowy"

__all__ = [
    'run'
]

__version__ = "0.1.0"

import logging
import os
import shutil

from bluesky import io
from bluesky.config import Config

def run(fires_manager):
    """runs the archive module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """


    tarzip(fires_manager)

def tarzip(fires_manager):
    dirs_to_tarzip = set()
    for m in Config().get('archive', 'tarzip'):
        info = getattr(fires_manager, m)
        if info and info.get('output', {}).get('directory'):
            logging.debug("Dir to tarzip: %s", info['output']['directory'])
            dirs_to_tarzip.add(info['output']['directory'])
    for d in dirs_to_tarzip:
        if os.path.exists(d):
            logging.debug("tarzipping: %s", d)
            io.create_tarball(d)
            shutil.rmtree(d)
