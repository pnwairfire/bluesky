"""bluesky.dispersers"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import abc
import copy
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

    # 'BINARIES' dict should be defined by each subclass which depend on
    # external binaries
    BINARIES = {}

    # 'DEFAULTS' object should be defined by each subclass that has default
    # configuration settings (such as in a defaults module)
    DEFAULTS = None

    def __init__(self, met_info, **config):
        self._set_met_info(copy.deepcopy(met_info))
        self._config = config
        # TODO: iterate through self.BINARIES.values() making sure each
        #   exists (though maybe only log warning if doesn't exist, since
        #   they might not all be called for each run
        # TODO: define and call method (which should rely on constant defined
        #   in model-specific classes) which makes sure all required config
        #   options are defined

    def config(self, key):
        # check if key is defined, in order, a) in the config as is, b) in
        # the config as lower case, c) in the hardcoded defaults
        return self._config.get(key,
            self._config.get(key.lower(),
                getattr(self.DEFAULTS, key, None)))

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
