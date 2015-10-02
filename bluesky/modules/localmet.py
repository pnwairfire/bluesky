"""bluesky.modules.localmet"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging

from pyairfire.datetime import parsing as datetime_parsing

from bluesky.airlprofiler import ArlProfiler
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

    arl_profiler = ArlProfiler(config.get(''))
    for fire in fires_manager.fires:
        lat,lng = _fire_lat_lng(fire)
        for g in fire.growth:
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
