__version__ = "0.1.0"

import datetime
import logging
import os

from pyairfire import osutils

from bluesky import io
from bluesky.metutils import filter_met
from .setup import ControlFileWriter
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
        self._locations = fires_manager.locations
        self._met = filter_met(fires_manager.met, start, num_hours)

    def run(self):
        aggregated = {}
        for s in self._config['start_hours']:
            try:
                output = self._run_start_hour(start_hour)
                # TODO: add to aggregated output
            except Exception as e:
                logging.error(
                    "Failed to compute trajectories for start_hour %s: %s", s, e)
                # TODO: somehow mark failure in aggregated data

        if not aggregated:
            # TODO: use BlueSkySubprocessError ?
            raise RuntimeError("Failed all hysplit trajectories runs")

        # TODO: write aggregated output to file in output dir

        r = {
            "start": start,
            "num_hours": num_hours,
            "output_dir": output_dir,
            "working_dir": working_dir,
            "config": self._config
            # TODO: include information about failures?
        }
        return r

    def _run_start_hour(self, start_hour):
        start_s = start + datetime.timedelta(hours=self._start_hour)
        working_dir_s = self._working_dir and os.path.join(
            self._working_dir, str(s))
        with osutils.create_working_dir(working_dir=working_dir_s) as wdir:
            ControlFileWriter(self._config).write(
                self._locations, start_s, self._num_hours, wdir)
            SetupFileWriter(self._config).write(wdir)
            self._sum_link_met_files(wdir)
            self._sym_link_static_files(wdir)
            self._run_hysplit(wdir)
            return OutputLoader(self._config).load(wdir)

    def _sym_link_met_files(self, wdir):
        for f in self._met_info['files']:
            # bluesky.modules.dispersion.run will have weeded out met
            # files that aren't relevant to this dispersion run
            self._create_sym_link(f,
                os.path.join(wdir, os.path.basename(f)))

    def _sym_link_static_files(self, wdir):
        for k, pathname in self._config['static_files']:
            link_pathname = os.path.join(wdir, os.path.basename(pathname))
            self._create_sym_link(pathname, link_pathname)

    def _run_hysplit(self, wdir):
        io.SubprocessExecutor().execute(
            self._config['binary'], cwd=wdir)
