"""bluesky.trajectories.hysplit"""

__version__ = "0.1.0"

import datetime
import logging
import os
import traceback

from afdatetime.parsing import parse_datetime, parse_utc_offset
from pyairfire import osutils

from bluesky import io
from bluesky.config import Config
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
            self._num_hours)
        self._setup_file_writer = SetupFileWriter(self._config)
        self._output_loader = OutputLoader(self._config)
        self._output_writer = JsonOutputWriter(self._config, fires_manager,
            self._output_dir)


    ## Public Interface

    def run(self):
        r = {
            "output": {
                'start': self._start,
                'num_hours': self._num_hours,
                'directory': self._output_dir
            }
        }

        if (not self._locations):
            msg = "Did not run HYSPLIT trajectories - no fire locations"
            logging.warn(msg)
            r['warning'] = msg

        else:
            num_failed = 0
            for start_hour in self._config['start_hours']:
                try:
                    logging.debug("Computing trajectories for start_hour %s",
                        start_hour)
                    self._run_start_hour(start_hour)

                except Exception as e:
                    num_failed += 1
                    logging.debug(traceback.format_exc())
                    logging.error(
                        "Failed to compute trajectories for start_hour %s: %s",
                        start_hour, e)
                    # TODO: somehow mark failure in output data

            self._output_writer.write()

            r["output"].update({
                "json_file_name": os.path.basename(self._output_writer.json_file_name),
                "geojson_file_name": os.path.basename(self._output_writer.geojson_file_name)
            })
            if num_failed:
                num_start_hours = len(self._config['start_hours'])
                if num_failed == num_start_hours:
                    r["error"] = "{} {} hysplit trajectories run{} failed".format(
                        "All" if num_failed > 1 else "The", num_failed,
                        "s" if num_failed > 1 else "")
                else:
                    r["warning"] = "{} of the {} hysplit trajectories runs failed".format(
                        num_failed, num_start_hours)
        return r


    ## Helpers

    def _run_start_hour(self, start_hour):
        start_s = self._start + datetime.timedelta(hours=start_hour)
        working_dir_s = self._working_dir and os.path.join(
            self._working_dir, str(start_hour))

        locations = self._filter_locations(start_s)
        if not locations:
            logging.warn("No activity at start hour %s. Skipping hysplit", start_s)
            return

        delete_if_no_error = Config().get(
            'trajectories', 'delete_working_dir_if_no_error')
        with osutils.create_working_dir(working_dir=working_dir_s,
                delete_if_no_error=delete_if_no_error) as wdir:
            met_files = self._get_met_files(start_s)
            self._control_file_writer.write(start_s, met_files, wdir, locations)
            self._setup_file_writer.write(wdir)
            self._sym_link_met_files(wdir, met_files)
            self._sym_link_static_files(wdir)
            self._run_hysplit(wdir)
            self._output_loader.load(start_s, wdir, locations)

    def _filter_locations(self, start_s):
        locations = [l for l in self._locations
            if parse_datetime(l._active_area['start']) <= start_s
            and parse_datetime(l._active_area['end']) > start_s]

        return locations

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
