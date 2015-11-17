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
        self._upload_options = {}
        # TODO: don't assume scp? maybe look for 'scp' > 'host' & 'user' & ...,
        #  and/or 'ftp' > ..., etc., and upload to all specified
        self._read_scp_config()
        # TODO: other upload options
        if not self._upload_options:
            raise BlueSkyConfigurationError("Specify at lease one mode of uploads")

    def _read_scp_config(self):
        c = self.config('scp'):
        if c:
            if any([not c.get(k) for k in ['user', 'host', 'dest_dir']):
                raise BlueSkyConfigurationError(
                    "Specify user, host, and dest_dir for scp'ing")
            self._upload_options['scp'] = c

    def _scp(self, tarball):
        if self._upload_options['scp']:
            # TODO: scp and then untar on remote server (using fabric or some
            #  other package).
            # TODO: return dict contaning where it's been uplaoded
            raise NotImplementedError("SCP not yet implemented")

    def export(self, fires_manager):
        with tempfile.TemporaryDirectory() as temp_dir:
            self._bundle(fires_manager, temp_dir.name, create_tarball=True)
            r = {
                'scp': self._scp(tarball)
                # TODO: implement and call other upload options
            }
            # Only include uploads that happened
            return {k: v for k,v in r.items() if v}
