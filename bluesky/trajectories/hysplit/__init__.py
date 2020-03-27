__version__ = "0.1.0"

import datetime
import logging
import os
import traceback

from pyairfire import osutils

from bluesky import io
from bluesky.metutils import filter_met
from .setup import ControlFileWriter, SetupFileWriter
from .load import OutputLoader
from .output import JsonOutputWriter

__all__ = [
    "HysplitTrajectories"
]

class HysplitTrajectories(object):

    def __init__(self, config, fires_manager, start, num_hours, output_dir,
            working_dir=None):
        self._config = config
        self._start = start
        self._num_hours = num_hours
        self._output_dir = output_dir
        self._working_dir = working_dir
        self._met = fires_manager.met
        self._locations = fires_manager.locations
        self._control_file_writer = ControlFileWriter(self._config,
            self._locations, self._num_hours)
        self._setup_file_writer = SetupFileWriter(self._config)
        self._output_loader = OutputLoader(self._config,
            fires_manager.locations)
        self._output_writer = JsonOutputWriter(self._config, fires_manager,
            self._output_dir)


    ## Public Interface

    def run(self):
        for start_hour in self._config['start_hours']:
            try:
                self._run_start_hour(start_hour)
            except Exception as e:
                logging.debug(traceback.format_exc())
                logging.error(
                    "Failed to compute trajectories for start_hour %s: %s",
                    start_hour, e)
                # TODO: somehow mark failure in aggregated data

        self._output_writer.write()

        r = {
            "start": self._start,
            "num_hours": self._num_hours,
            "output_dir": self._output_dir,
            "working_dir": self._working_dir,
            "config": self._config
            # TODO: include information about failures?
        }
        return r


    ## Helpers

    def _run_start_hour(self, start_hour):
        start_s = self._start + datetime.timedelta(hours=start_hour)
        working_dir_s = self._working_dir and os.path.join(
            self._working_dir, str(start_hour))
        with osutils.create_working_dir(working_dir=working_dir_s) as wdir:
            met_files = self._get_met_files(start_s)
            self._control_file_writer.write(start_s, met_files, wdir)
            self._setup_file_writer.write(wdir)
            self._sym_link_met_files(wdir, met_files)
            self._sym_link_static_files(wdir)
            self._run_hysplit(wdir)
            self._output_loader.load(start_s, wdir)

    def _get_met_files(self, start):
        met = filter_met(self._met, start, self._num_hours)
        return sorted([f['file'] for f in met['files']])

    def _sym_link_met_files(self, wdir, met_files):
        for f in met_files:
            io.create_sym_link(f, os.path.join(wdir, os.path.basename(f)))

    def _sym_link_static_files(self, wdir):
        for k, pathname in self._config['static_files'].items():
            link_pathname = os.path.join(wdir, os.path.basename(pathname))
            io.create_sym_link(pathname, link_pathname)

    def _run_hysplit(self, wdir):
        io.SubprocessExecutor().execute(
            self._config['binary'], cwd=wdir)
