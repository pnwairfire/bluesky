"""bluesky.modules.splitactivity"""

__author__ = "Joel Dubowy"

import copy
import logging

from bluesky.config import Config

__all__ = [
    'run'
]

__version__ = "0.1.0"


def run(fires_manager):
    """Split each of the fire's activity windows to be able to process points
    separately.

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running merge module")
    fires_manager.processed(__name__, __version__)
    record_original_activity = Config.get(
        'splitactivity', 'record_original_activity')

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            _split(fire, record_original_activity)

def _split(fire, record_original_activity):
    new_activity = []
    for g in fire.get('activity', []):
        new_activity.extend(_split_activity(g))

    if new_activity and new_activity != fire['activity']:  #len(new_activity) != len(fire['activity']):
        if record_original_activity:
            fire['original_activity'] = fire['activity']
        fire['activity'] = new_activity

# TODO: Support splitting these fields. Only fuelbeds would
#   be a bit of work to split. For 'consumption', 'emissions',
#   and 'heat', just recursive to divide numeric values
CANT_SPLIT_FIELDS = [
    'consumption', 'emissions', 'fuelbeds', 'heat'
]

def _split_activity(g):
    try:
        geojson = g.get('location', {}).get('geojson')
        if geojson:
            if not any([k in g for k in CANT_SPLIT_FIELDS]):
                func_name = '_split_{}'.format(geojson.get('type','').lower())
                f = globals().get(func_name)
                if f:
                     return f(g)
                else:
                    logging.debug("splitactivity doesn't support GeoJSON type %s",
                        geojson.get('type', '(not specified)'))
            else:
                logging.warning("split activity ")
        else:
            logging.debug("splitactivity only supports GeoJSON geometries")
    except:
        logging.warning("Failed to split activity %s", g)

    return [g]

def _split_multipoint(g):
    logging.debug('splitting multipoint activity object')
    activity = []
    for coord in g['location']['geojson']['coordinates']:
        new_g = copy.deepcopy(g)
        new_g['location']['geojson']['type'] = 'Point'
        new_g['location']['geojson']['coordinates'] = coord
        if new_g['location'].get('area'):
            new_g['location']['area'] /= len(g['location']['geojson']['coordinates'])
        activity.append(new_g)
    return activity

def _split_multipolygon(g):
    if not g['location'].get('area'):
        activity = []
        for polygon in g['location']['geojson']['coordinates']:
            new_g = copy.deepcopy(g)
            new_g['location']['geojson']['type'] = 'Polygon'
            new_g['location']['geojson']['coordinates'] = polygon
            activity.append(new_g)
        return activity
    return [g]
