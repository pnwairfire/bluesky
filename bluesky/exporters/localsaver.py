# TODO: look at config>export>local>dest, which hsould be root dir to contain
#   output dir, or outputdir itself (?).  If root dir containing, then also
#   suport specifying a run_id, which is generated if not specified (could also
#   look at dispersion or visualization run_id, if they're in data)

# TODO: dump fires_manager to json (configurable dir and filename)


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
        self._dest = self.config('dest')
        if not self._dest:
            raise BlueSkyConfigurationError("Specify destination "
                "('config' > 'localsave' > 'dest')")

    def export(self, fires_manager):
        logging.info('Saving locally to %s', self._dest)
        d = self._bundle(fires_manager, create_tarball=False)
        # TODO: move d to self._dest
        return {
            'dest': os.path.join(self._dest, os.path.basename(d.rstrip('/')))
        }
