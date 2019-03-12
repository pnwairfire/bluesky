"""bluesky.modules.localmet

This module relies on the fortran arl profile utility. It is expected to
reside in a directory in the search path. (This module prevents configuring
relative or absolute paths to profile, to eliminiate security vulnerabilities
when invoked by web service request.) To obtain profile, contact NOAA.
"""

__author__ = "Joel Dubowy"

import logging
import os

from met.arl.arlprofiler import ArlProfiler

from bluesky.config import Config
from bluesky.datetimeutils import parse_datetimes, parse_utc_offset
from bluesky.locationutils import LatLng

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running localmet module")
    fires_manager.processed(__name__, __version__)
    if not fires_manager.met:
        raise ValueError("Specify met files to use in localmet")

    arl_profiler = ArlProfiler(fires_manager.met.get('files'),
        time_step=Config.get('localmet', 'time_step'))
    logging.debug("Extracting localmet data for %d fires",
        len(fires_manager.fires))
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            if not fire.get('growth'):
                raise ValueError("Missing growth data required for localmet")
            for g in fire['growth']:
                latlng = LatLng(g.get('location'))
                # parse_utc_offset makes sure utc offset is defined and valid
                utc_offset = parse_utc_offset(g.get('location', {}).get('utc_offset'))
                tw = parse_datetimes(g, 'start', 'end')
                g['localmet'] = arl_profiler.profile(latlng.latitude,
                    latlng.longitude, tw['start'],
                    tw['end'], utc_offset)

    # fires_manager.summarize(...)
