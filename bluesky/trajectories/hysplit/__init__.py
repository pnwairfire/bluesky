__version__ = "0.1.0"

from pyairfire import osutils

from bluesky.metutils import filter_met
from .setup import ControlFileWriter
from .output import OutputLoader


class HysplitTrajectories(object):

    def __init__(config):
        self._config = config

    def run(self, fires_manager, start, num_hours, output_dir,
            working_dir=working_dir):
        met = filter_met(fires_manager.met, start, num_hours)

        with osutils.create_working_dir(working_dir=working_dir) as wdir:
            ControlFileWriter(self._config).write(start, num_hours, wdir)
            self._run_hysplit()
            output = OutputLoader(self._config).load(wdir)
            return output

    def _run_hysplit(self):
        pass
