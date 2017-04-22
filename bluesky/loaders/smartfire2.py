"""bluesky.loaders.smartfire
"""

__author__ = "Joel Dubowy"

import os

from . import BaseCsvFileLoader

__all__ = [
    'CsvFileLoader'
]

class CsvFileLoader(BaseCsvFileLoader):
    """Loads csv formatted SF2 fire and events data from filename

    Nothing in the base class needs to be overridden.
    """
    pass
