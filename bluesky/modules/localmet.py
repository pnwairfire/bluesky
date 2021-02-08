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

    start_utc = None
    end_utc = None

    # keep array of references to locations passed into arlprofiler,
    # to update with local met data after bulk profiler is called
    locations = []
    # actual array of locations to pass into arlprofiler
    profiler_locations = []
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
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
                start_utc = min(start_utc, loc_start_utc) if start_utc else loc_start_utc

                loc_end_utc = tw['end'] - datetime.timedelta(hours=utc_offset)
                end_utc = min(end_utc, loc_end_utc) if end_utc else loc_end_utc

                for loc in aa.locations:
                    latlng = LatLng(loc)
                    p_loc = {
                        'latitude': latlng.latitude,
                        'longitude': latlng.longitude
                    }

                    locations.append(loc)
                    profiler_locations.append(p_loc)

    if len(locations) != len(profiler_locations):
        raise RuntimeError(FAILED_TO_COMPILE_INPUT_ERROR_MSG)

    if not start_utc or not end_utc:
        raise RuntimeError(NO_START_OR_END_ERROR_MSG)

    arl_profiler = arlprofiler.ArlProfiler(fires_manager.met.get('files'),
        time_step=Config().get('localmet', 'time_step'))
    logging.debug("Extracting localmet data for %d locations",
        len(profiler_locations))

    localmet = arl_profiler.profile(
        start_utc, end_utc, profiler_locations)

    if len(localmet) != len(locations):
        raise RuntimeError(PROFILER_RUN_ERROR_MSG)

    for i in range(len(localmet)):
        locations[i]['localmet'] = localmet[i]

    # fires_manager.summarize(...)
