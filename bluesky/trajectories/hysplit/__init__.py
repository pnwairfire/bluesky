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

    def __init__(self, config):
        self._config = config

    def run(self, fires_manager, start, num_hours, output_dir,
            working_dir=None):
        met = filter_met(fires_manager.met, start, num_hours)

        output = {}
        for s in self._config['start_hours']:
            try:
                start_s = start + datetime.timedelta(hours=s)
                working_dir_s = working_dir and os.path.join(working_dir, str(s))
                with osutils.create_working_dir(working_dir=working_dir_s) as wdir:
                    ControlFileWriter(self._config).write(fires_manager.locations,
                        start_s, num_hours, wdir)
                    self._run_hysplit(wdir)
                    output = OutputLoader(self._config).load(wdir)
                    # TODO: add to aggregated output
            except Exception as e:
                logging.error(
                    "Failed to compute trajectories for start_hour %s: %s", s, e)
                # TODO: somehow mark failure in aggregated data

        if not output:
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

    def _run_hysplit(self, wdir):
        io.SubprocessExecutor().execute(
            self._config['binary'], cwd=wdir)
