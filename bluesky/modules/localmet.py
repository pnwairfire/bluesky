"""bluesky.modules.localmet

This module relies on the fortran arl profile utility. It is expected to
reside in a directory in the search path. (This module prevents configuring
relative or absolute paths to profile, to eliminiate security vulnerabilities
when invoked by web service request.) To obtain profile, contact NOAA.
"""

__author__ = "Joel Dubowy"

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

def run(fires_manager):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    fires_manager.processed(__name__, __version__)
    if not fires_manager.met:
        raise ValueError(NO_MET_ERROR_MSG)

    arl_profiler = arlprofiler.ArlProfiler(fires_manager.met.get('files'),
        time_step=Config().get('localmet', 'time_step'))
    logging.debug("Extracting localmet data for %d fires",
        len(fires_manager.fires))
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            # Make sure fire has at least some locations, but
            # iterate first through activice areas and then through
            # locations in order to get utc_offset and time windows
            if not fire.locations:
                raise ValueError(NO_ACTIVITY_ERROR_MSG)

            for aa in fire.active_areas:
                utc_offset = parse_utc_offset(aa.get('utc_offset'))
                tw = parse_datetimes(aa, 'start', 'end')
                for loc in aa.locations:
                    latlng = LatLng(loc)
                    # parse_utc_offset makes sure utc offset is defined and valid
                    loc['localmet'] = arl_profiler.profile(latlng.latitude,
                        latlng.longitude, tw['start'],
                        tw['end'], utc_offset)

    # fires_manager.summarize(...)
