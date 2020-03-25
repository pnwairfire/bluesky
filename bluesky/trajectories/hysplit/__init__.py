__version__ = "0.1.0"

import datetime
import logging
import os
import traceback

from pyairfire import osutils

from bluesky import io
from bluesky.metutils import filter_met
from .setup import ControlFileWriter, SetupFileWriter
from .output import OutputLoader

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
        self._set_met_files(fires_manager.met)
        self._control_file_writer = ControlFileWriter(self._config,
            self._met_files, fires_manager.locations, self._num_hours)
        self._setup_file_writer = SetupFileWriter(self._config)


    ## Public Interface

    def run(self):
        aggregated = {}
        for start_hour in self._config['start_hours']:
            try:
                output = self._run_start_hour(start_hour)
                # TODO: add to aggregated output
            except Exception as e:
                logging.debug(traceback.format_exc())
                logging.error(
                    "Failed to compute trajectories for start_hour %s: %s",
                    start_hour, e)
                # TODO: somehow mark failure in aggregated data

        if not aggregated:
            # TODO: use BlueSkySubprocessError ?
            raise RuntimeError("Failed all hysplit trajectories runs")

        # TODO: write aggregated output to file in output dir

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

    def _set_met_files(self, met_info):
        # filter_met weeds out met files that aren't relevant to this run
        met_info = filter_met(met_info, self._start, self._num_hours)
        self._met_files = sorted([f['file'] for f in met_info['files']])

    def _run_start_hour(self, start_hour):
        start_s = self._start + datetime.timedelta(hours=start_hour)
        working_dir_s = self._working_dir and os.path.join(
            self._working_dir, str(start_hour))
        with osutils.create_working_dir(working_dir=working_dir_s) as wdir:
            self._control_file_writer.write(start_s, wdir)
            self._setup_file_writer.write(wdir)
            self._sym_link_met_files(wdir)
            self._sym_link_static_files(wdir)
            self._run_hysplit(wdir)
            return OutputLoader(self._config).load(wdir)

    def _sym_link_met_files(self, wdir):
        for f in self._met_files:
            io.create_sym_link(f, os.path.join(wdir, os.path.basename(f)))

    def _sym_link_static_files(self, wdir):
        for k, pathname in self._config['static_files'].items():
            link_pathname = os.path.join(wdir, os.path.basename(pathname))
            io.create_sym_link(pathname, link_pathname)

    def _run_hysplit(self, wdir):
        io.SubprocessExecutor().execute(
            self._config['binary'], cwd=wdir)
