"""bluesky.modules.localmet

This module relies on the fortran arl profile utility. It is expected to
reside in a directory in the search path. (This module prevents configuring
relative or absolute paths to profile, to eliminiate security vulnerabilities
when invoked by web service request.) To obtain profile, contact NOAA.
"""

__author__ = "Joel Dubowy"

import datetime
import logging
import os
import shutil

from met.arl import arlprofiler

from bluesky.config import Config
from bluesky.datetimeutils import parse_datetimes, parse_utc_offset
from bluesky.locationutils import LatLng

__all__ = [
    'run'
]

__version__ = "0.1.0"

NO_MET_ERROR_MSG = "Specify met files to use in localmet"
NO_ACTIVITY_ERROR_MSG = "Missing activity location data required for localmet"
FAILED_TO_COMPILE_INPUT_ERROR_MSG = "Failed to compile input to run localmet profiler"
NO_START_OR_END_ERROR_MSG = "Couldn't determine start and/or end time for localmet profiling"
PROFILER_RUN_ERROR_MSG = "Failure in localmet profiling"

def run(fires_manager):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    fires_manager.processed(__name__, __version__)
    if not fires_manager.met:
        raise ValueError(NO_MET_ERROR_MSG)

    if not fires_manager.fires:
        logging.warning("No fires to run localmet")
        return


    LocalmetRunner(fires_manager).run()

    # fires_manager.summarize(...)


class LocalmetRunner(object):

    def __init__(self, fires_manager):
        self._fires_manager = fires_manager
        self._start_utc = None
        self._end_utc = None
        self._skip_failures = Config().get('localmet', 'skip_failures')

        # keep array of references to locations passed into arlprofiler,
        # to update with local met data after bulk profiler is called
        self._locations = []

        # actual array of locations to pass into arlprofiler
        self._profiler_locations = []

        self._compile()
        self._validate()

    @property
    def start_utc(self):
        return self._start_utc

    @property
    def end_utc(self):
        return self._end_utc

    @property
    def locations(self):
        return self._locations

    @property
    def profiler_locations(self):
        return self._profiler_locations

    def run(self):
        working_dir = Config().get('localmet', 'working_dir')
        arl_profiler = arlprofiler.ArlProfiler(
            self._fires_manager.met.get('files'),
            time_step=Config().get('localmet', 'time_step'),
            working_dir=working_dir)
        logging.debug("Extracting localmet data for %d locations",
            len(self._profiler_locations))

        try:
            localmet = arl_profiler.profile(
                self._start_utc, self._end_utc, self._profiler_locations)
        except:
            if self._skip_failures:
                return
            raise

        if len(localmet) != len(self._locations):
            if self._skip_failures:
                return
            raise RuntimeError(PROFILER_RUN_ERROR_MSG)

        for i in range(len(localmet)):
            self._locations[i]['localmet'] = localmet[i]

        if (working_dir and Config().get('localmet', 'delete_working_dir_if_no_error')):
            try:
                logging.debug('Deleting localmet working dir %s', working_dir)
                shutil.rmtree(working_dir)

            except Exception as e:
                logging.warn('Failed to delete localmet working dir %s', working_dir)


    def _compile(self):
        for fire in self._fires_manager.fires:
            with self._fires_manager.fire_failure_handler(fire):
                # Make sure fire has at least some locations, but
                # iterate first through activice areas and then through
                # locations in order to get utc_offset and time windows
                if not fire.locations:
                    raise ValueError(NO_ACTIVITY_ERROR_MSG)

                for aa in fire.active_areas:
                    # parse_utc_offset makes sure utc offset is defined and valid
                    utc_offset = parse_utc_offset(aa.get('utc_offset'))
                    tw = parse_datetimes(aa, 'start', 'end')

                    # subtract utc_offset, since we want to get back to utc
                    loc_start_utc = tw['start'] - datetime.timedelta(hours=utc_offset)
                    self._start_utc = min(self._start_utc, loc_start_utc) if self._start_utc else loc_start_utc

                    loc_end_utc = tw['end'] - datetime.timedelta(hours=utc_offset)
                    self._end_utc = min(self._end_utc, loc_end_utc) if self._end_utc else loc_end_utc

                    for loc in aa.locations:
                        latlng = LatLng(loc)
                        p_loc = {
                            'latitude': latlng.latitude,
                            'longitude': latlng.longitude
                        }

                        self._locations.append(loc)
                        self._profiler_locations.append(p_loc)

    def _validate(self):
        if len(self._locations) != len(self._profiler_locations):
            raise RuntimeError(FAILED_TO_COMPILE_INPUT_ERROR_MSG)

        if not self._start_utc or not self._end_utc:
            raise RuntimeError(NO_START_OR_END_ERROR_MSG)
