"""bluesky.modules.localmet

This module relies on the fortran arl profile utility. It is expected to
reside in a directory in the search path. (This module prevents configuring
relative or absolute paths to profile, to eliminiate security vulnerabilities
when invoked by web service request.) To obtain profile, contact NOAA.

"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import os

from bluesky.met.arlprofiler import ArlProfiler
from bluesky.datetimeutils import parse_datetimes

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager, config=None):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    logging.info("Running localmet module")
    fires_manager.processed(__name__, __version__)

    for fire in fires_manager.fires:
        lat,lng = _fire_lat_lng(fire)
        # TODO: make sure fire.location['timezone'] is defined and valid
        # TODO: rename 'timezone' as something like utc_offset ?
        # TODO: parse utc offset from fire.location['timezone']
        utc_offset = 0
        for g in fire.growth:
            # Note: ArlProfiler will raise an exception if met_root_dir is undefined
            # or is not a valid directory
            # TODO: shoudl met_files be specifeid in config, to apply to all fires?
            arl_profiler = ArlProfiler(g.get('met_files'))
            g['localmet'] = arl_profiler.profile(lat, lng, utc_offset)
            # TODO: make sure entire growth window is covered (and no more?);
            #  use tw = parse_datetimes(g, 'start', 'end') to parse growth window

    # fires_manager.summarize(...)

def _fire_lat_lng(fire):
    if not fire.get('location'):
        raise ValueError(
            "Missing location data required for looking up localmet data")

    if fire['location'].get('perimeter'):
        # TODO: get centroid of perimeter(s); also, can'st assume 3-deep nested
        # array (it's 3-deep for MultiPolygon, but not necessarily other shape types)
        lat = fire['location']['perimeter']['coordinates'][0][0][0][1]
        lng = fire['location']['perimeter']['coordinates'][0][0][0][0]
    elif fire['location'].get('latitude') and fire['location'].get('longitude'):
        lat = fire['location']['latitude']
        lng = fire['location']['longitude']
    elif fire['location'].get('shape_file'):
        raise NotImplementedError("Importing of shape data from file not implemented")
    else:
        raise ValueError(
            "Insufficient location data required for looking up lcalmet data")

    return (lat, lng)
