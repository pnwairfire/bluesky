"""bluesky.dispersers"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import abc
import logging
import os
import tempfile

# TODO: move this to common/reusable module
class working_dir(object):
    def __enter__(self):
        self._original_dir = os.getcwd()
        self._working_dir = tempfile.mkdtemp()
        logging.debug('Running hysplit in {}'.format(self._working_dir))
        os.chdir(self._working_dir)
        return self._working_dir

    def __exit__(self, type, value, traceback):
        os.chdir(self._original_dir)
        # TODO: delete self._working_dir or just let os clean it up ?

class DispersionBase(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def run(self, fires, start, num_hours, dest_dir, output_dir_name):
        """Runs hysplit

        args:
         - fires - list of fires to run through hysplit
         - start - model run start hour
         - num_hours - number of hours in model run
         - dest_dir - directory to contain output dir
         - output_dir_name - name of output dir
        """
        pass
