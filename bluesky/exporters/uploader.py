"""bluesky.exporters.uploader"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import os
import shutil
import subprocess
import tempfile

from bluesky.exceptions import BlueSkyConfigurationError
from . import ExporterBase

__all__ = [
    'UploadExporter'
]

__version__ = "0.1.0"

DEFAULT_SCP_USER = "bluesky"
DEFAULT_SCP_PORT = 22

class UploadExporter(ExporterBase):

    def __init__(self, extra_exports, **config):
        super(UploadExporter, self).__init__(extra_exports, **config)
        self._upload_options = {}
        # TODO: don't assume scp? maybe look for 'scp' > 'host' & 'user' & ...,
        #  and/or 'ftp' > ..., etc., and upload to all specified
        self._read_scp_config()
        # TODO: other upload options
        if not self._upload_options:
            raise BlueSkyConfigurationError("Specify at lease one mode of uploads")

    def _read_scp_config(self):
        c = self.config('scp')
        if c:
            if any([not c.get(k) for k in ['user', 'host', 'dest_dir']]):
                raise BlueSkyConfigurationError(
                    "Specify user, host, and dest_dir for scp'ing")
            self._upload_options['scp'] = c

    def _scp(self, tarball):
        if self._upload_options['scp']:
            port = self._upload_options['scp']['port'] or DEFAULT_SCP_PORT
            remote_server = "{}@{}".format(
                self._upload_options['scp']['user'] or DEFAULT_SCP_USER,
                self._upload_options['scp']['host'])
            destination = "{}:{}".format(remote_server,
                self._upload_options['scp']['dest_dir'])
            try:
                # Note: there are various ways of doing this: a) call scp directly,
                #  b) use paramiko, c) use fabric, d) etc.....
                #  See http://stackoverflow.com/questions/68335/how-do-i-copy-a-file-to-a-remote-server-in-python-using-scp-or-ssh
                #  for examples
                logging.info("Creating remote destination {}".format(
                    self._upload_options['scp']['dest_dir']))
                subprocess.check_call(['ssh', remote_server, '-p', port,
                    'mkdir', '-p', self._upload_options['scp']['dest_dir']])
                logging.info("Uploading {} via scp".format(tarball))
                subprocess.check_call(['scp', '-P', port, tarball, destination])
            except Exception, e:
                return {"error": "failed to upload {} - {}".format(tarball,
                    e.message)}

            r = {
                "destination": destination,
                "tarball": os.path.basename(tarball)
            }

            # TODO: move extraction code to separate method, to share with other
            #  future upload modes
            try:
                tarball_filename = os.path.basename(tarball)
                logging.info("Extracting {}".format(tarball))
                subprocess.check_call(['ssh', remote_server, '-p', port,
                    'cd', self._upload_options['scp']['dest_dir'], '&&',
                    'tar', 'xzf', tarball_filename])
                r["directory"] = self._output_dir_name
            except:
                r["error"] = "failed to extract {}".format(tarball)


    def export(self, fires_manager):
        with tempfile.TemporaryDirectory() as temp_dir:
            self._bundle(fires_manager, temp_dir.name, create_tarball=True)
            r = {
                'scp': self._scp(tarball)
                # TODO: implement and call other upload options
            }
            # Only include uploads that happened
            return {k: v for k,v in r.items() if v}
