"""bluesky.dispersers

TODO: Move this package into it's own repo. One thing that would need to be
done first is to remove the dependence on bluesky.models.fires.Fire.
This would be fairly easy, since Fire objects are for the most part dicts.
Attr access of top level keys would need to be replaced with direct key
access, and the logic in Fire.latitude and Fire.longitude would need to be
moved into hysplit.py.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import abc
import copy
import logging
import os
import tempfile

# TODO: move this to common/reusable module
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

    def run(self, fires, start, num_hours, dest_dir, output_dir_name):
        """Runs hysplit

        args:
         - fires - list of fires to run through hysplit
         - start - model run start hour
         - num_hours - number of hours in model run
         - dest_dir - directory to contain output dir
         - output_dir_name - name of output dir
        """
        logging.info("Running %s", self.__class__.__name__)
        if start.minute or start.second or start.microsecond:
            raise ValueError("Dispersion start time must be on the hour.")
        if type(num_hours) != int:
            raise ValueError("Dispersion num_hours must be an integer.")
        self._model_start = start
        self._num_hours = num_hours

        self._run_output_dir = os.path.join(os.path.abspath(dest_dir),
            output_dir_name)
        os.makedirs(self._run_output_dir)

        self._files_to_archive = []


        with create_working_dir() as wdir:
            r = self._run(fires, wdir)
            self._move_files()

        r.update({
            "directory": self._run_output_dir,
            "start_time": self._model_start.isoformat(),
            "num_hours": self._num_hours
        })
        return r

    @abc.abstractmethod
    def _run(fires, wdir):
        """Underlying run method to be implemented by subclasses

        args:
         - fires - list of fires to run through hysplit
        """
        pass


    def _save_file(self, file):
        self._files_to_archive.append(file)

    def _move_files(self):
        for f in self._files_to_archive:
            shutil.move(f, self._run_output_dir)
