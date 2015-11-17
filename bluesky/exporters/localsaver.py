"""bluesky.exporters.uploader"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from bluesky.exceptions import BlueSkyConfigurationError
from . import ExporterBase

__all__ = [
    'LocalSaveExporter'
]

__version__ = "0.1.0"

class LocalSaveExporter(ExporterBase):

    def __init__(self, extra_exports, **config):
        super(EmailExporter, self).__init__(extra_exports, **config)
        self._dest = self.config('dest_dir')
        if not self._dest:
            raise BlueSkyConfigurationError("Specify destination "
                "('config' > 'export' > 'localsave' > 'dest_dir')")

    def export(self, fires_manager):
        logging.info('Saving locally to %s', self._dest)
        # TODO: move d to self._dest
        return {
            'directory': self._bundle(fires_manager, self._dest)
        }
