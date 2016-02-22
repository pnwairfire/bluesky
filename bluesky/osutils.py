"""bluesky.io"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import logging
import os
import tempfile

class create_working_dir(object):
    def __enter__(self):
        self._original_dir = os.getcwd()
        self._working_dir = tempfile.mkdtemp()
        logging.debug('Running hysplit in {}'.format(self._working_dir))
        os.chdir(self._working_dir)
        return self._working_dir

    def __exit__(self, type, value, traceback):
        os.chdir(self._original_dir)
        # TODO: delete self._working_dir or just let os clean it up ?
