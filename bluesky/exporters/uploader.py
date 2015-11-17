# TODO: look at config>export>upload>remote_dest, which should be root dir to contain
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
    'UploadExporter'
]

__version__ = "0.1.0"

DEFAULT_SCP_USER = "bluesky"

class UploadExporter(ExporterBase):

    def __init__(self, extra_exports, **config):
        super(EmailExporter, self).__init__(extra_exports, **config)
        # TODO: don't assume scp? maybe look for 'scp' > 'host' & 'user' & ...,
        #  and/or 'ftp' > ..., etc., and upload to all specified
        self._read_scp_config()

    def _read_scp_config(self):
        self._scp_config = self.config('scp'):
        if self._scp_config:
            if not self._scp_config.get('user') or not self._config.get('host')
                    or not self._config.get('dest_dir'):
                raise BlueSkyConfigurationError(
                    "Specify user, host, and dest_dir for scping")

    def _sep(self):
        if self._scp_config:


    def export(self, fires_manager):
        logging.info('Saving locally to %s', self._host)
        self._scp()
        # TODO: implement other upload options
