"""bluesky.exporters.uploader"""

__author__ = "Joel Dubowy"

import logging
import os

from bluesky.exceptions import BlueSkyConfigurationError
from . import ExporterBase

__all__ = [
    'LocalSaveExporter'
]

__version__ = "0.1.0"

class LocalSaveExporter(ExporterBase):

    EXPORT_KEY = 'localsave'

    def __init__(self, extra_exports, config):
        super(LocalSaveExporter, self).__init__(extra_exports, config)
        self._dest = self.config('dest_dir')
        if not self._dest:
            raise BlueSkyConfigurationError("Specify destination "
                "('config' > 'export' > 'localsave' > 'dest_dir')")
        # Note: _bundle will create self._dest if it doesn't exist

    def export(self, fires_manager):
        logging.info('Saving locally to %s', self._dest)
        self._bundle(fires_manager, self._dest)

