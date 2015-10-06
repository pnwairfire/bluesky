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

from bluesky.met.airlprofiler import ArlProfiler
from bluesky.datautils import parse_datetimes

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
        for g in fire.growth:
            # Note: ArlProfiler will raise an exception if met_root_dir is undefined
            # or is not a valid directory
            # TODO: shoudl met_files be specifeid in config, to apply to all fires?
            met_files = _parse_met_files(g.get('met_files'))
            arl_profiler = arlprofiler.ArlProfiler(met_files)
            tw = parse_datetimes(g, 'start', 'end')
            g['localmet'] = arl_profiler.profile(tw['start'], tw['end'], lat, lng)

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

def _parse_met_files(met_files):
    """Converts array of arl file w/ time range items to hash of hour to arl
    file.  Also validates data.
    """
    _met_files = {}
    for f_dict in met_files:
        tw = parse_datetimes(f_dict, 'start', 'end')
        f = f_dict.get("file")
        # TODO: make sure start/end are even hours
        if not f or not os.path.isfile(f):
            raise ValueError("{} is not a valid file".format(f))
        # TODO:
        #  - for each hour from start to end (including end?)
        #     - if hour is already in _met_files, raise exception (overlapping coverage)
        #     - _met_files[hour datetime object] = f_dict[]

    pass _met_files