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
        fire["growth"] = []
        for g in growth:
            fire['growth'].extend(_split_growth(g))

    if new_growth:
        if record_original_growth:
            fire['original_growth'] = fire['growth'])
        fire['growth'] = new_growth

# TODO: Support splitting these fields. Only fuelbeds would
#   be a bit of work to split. For 'consumption', 'emissions',
#   and 'heat', just recursive to divide numeric values
CANT_SPLIT_FIELDS = [
    'consumption', 'emissions', 'fuelbeds', 'heat'
]

def _split_growh(g):
    try:
        geojson = g.get('location', {}).get('geojson')
        if geojson:
            if not any([k in g for k in CANT_SPLIT_FIELDS]):
                f = getattr('_split_{}'.format(geojson.get('type','').lower())
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
    return

def _split_multipolygon(g):
    ## How to divide area between polygon????
    logging.debug('splitting multipolygon growth object')
    return
