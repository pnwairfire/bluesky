"""bluesky.modules.splitgrowth"""

__author__ = "Joel Dubowy"

import copy
import logging

__all__ = [
    'run'
]

__version__ = "0.1.0"


def run(fires_manager):
    """Split each of the fire's growth windows to be able to process points
    separately.

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running merge module")
    fires_manager.processed(__name__, __version__)
    skip_unsupported = fires_manager.get_config_value(
        'splitgrowth', 'record_original_growth')

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            _split(fire, record_original_growth)

def _split(fire, record_original_growth):
    new_growth = []
    for g in fire.get('growth', []):
        new_growth.extend(_split_growth(g))

    if new_growth and new_growth != fire['growth']:  #len(new_growth) != len(fire['growth']):
        if record_original_growth:
            fire['original_growth'] = fire['growth']
        fire['growth'] = new_growth

# TODO: Support splitting these fields. Only fuelbeds would
#   be a bit of work to split. For 'consumption', 'emissions',
#   and 'heat', just recursive to divide numeric values
CANT_SPLIT_FIELDS = [
    'consumption', 'emissions', 'fuelbeds', 'heat'
]

def _split_growth(g):
    try:
        geojson = g.get('location', {}).get('geojson')
        if geojson:
            if not any([k in g for k in CANT_SPLIT_FIELDS]):
                func_name = '_split_{}'.format(geojson.get('type','').lower())
                f = globals().get(func_name)
                if f:
                     return f(g)
                else:
                    logging.debug("splitgrowth doesn't support GeoJSON type %s",
                        geojson.get('type', '(not specified)'))
            else:
                logging.warn("split growth ")
        else:
            logging.debug("splitgrowth only supports GeoJSON geometries")
    except:
        logging.warn("Failed to split growth %s", g)

    return [g]

def _split_multipoint(g):
    logging.debug('splitting multipoint growth object')
    growth = []
    for coord in g['location']['geojson']['coordinates']:
        new_g = copy.deepcopy(g)
        new_g['location']['geojson']['type'] = 'Point'
        new_g['location']['geojson']['coordinates'] = coord
        if new_g['location'].get('area'):
            new_g['location']['area'] /= len(g['location']['geojson']['coordinates'])
        growth.append(new_g)
    return growth

def _split_multipolygon(g):
    if not g['location'].get('area'):
        growth = []
        for polygon in g['location']['geojson']['coordinates']:
            new_g = copy.deepcopy(g)
            new_g['location']['geojson']['type'] = 'Polygon'
            new_g['location']['geojson']['coordinates'] = polygon
            growth.append(new_g)
        return growth
    return [g]
