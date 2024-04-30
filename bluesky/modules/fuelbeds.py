"""bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import logging
import random
from collections import defaultdict

import fccsmap
from fccsmap.lookup import FccsLookUp
from functools import reduce

from bluesky.config import Config
from bluesky.locationutils import LatLng

__all__ = [
    'run'
]

__version__ = "0.1.0"


def create_lookup_objects():
    fccs_lookups = []

    for f in Config().get('fuelbeds', 'fccs_fuelload_files'):
        options = dict(**Config().get('fuelbeds'), fccs_fuelload_file=f)
        fccs_lookups.append(FccsLookUp(**options))

    for ts in Config().get('fuelbeds', 'fccs_fuelload_tile_sets'):
        options = dict(**Config().get('fuelbeds'),
            tiles_directory=ts.get('directory'),
            index_shapefile=ts.get('index_shapefile'))
        fccs_lookups.append(FccsLookUp(**options))

    if not fccs_lookups:
        fccs_lookups = [
            FccsLookUp(is_alaska=False, **Config().get('fuelbeds')), # Lower 48
            FccsLookUp(is_alaska=True, **Config().get('fuelbeds')) # AK
        ]

    return fccs_lookups

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    fires_manager.processed(__name__, __version__,
        fccsmap_version=fccsmap.__version__)

    logging.debug('Using FCCS version %s',
        Config().get('fuelbeds', 'fccs_version'))

    skip_failures = Config().get('fuelbeds', 'skip_failures')

    # Look up Objects need to be instantiated each time run is called in case
    # the configuration changes from run to run (as happens in bluesky-web)
    fccs_lookups = create_lookup_objects()

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for aa in fire.active_areas:
                # Note that aa.locations validates that each location object
                # has either lat+lng+area or perimeter
                for loc in aa.locations:
                    # try each lookup object until one succeeds
                    for lookup in fccs_lookups:
                        try:
                            Estimator(lookup).estimate(loc)
                            break
                        except Exception as e:
                            pass

                    if not loc.get('fuelbeds'):
                        latlng = LatLng(loc)
                        msg = ("Failed to lookup fuelbeds information for "
                            f"loc {latlng.latitude}, {latlng.longitude} ")
                        logging.error(msg)
                        if not skip_failures:
                            raise RuntimeError(msg)


    # TODO: Add fuel loadings data to each fuelbed object (????)
    #  If we do so here, use bluesky.modules.consumption.FuelLoadingsManager
    #  (which should maybe be moved to a common module if to be used here)
    #     fm = FuelLoadingsManager()
    #     for fire in fires_manager.fires:
    #       for fb in get_fuel_loadings():
    #         fb['fuel_loadings'] = fm.get_fuel_loadings(fb['fccs_id'])
    #  Note: probably no need to do this here since we do it in the
    #  consumption module

    fires_manager.summarize(fuelbeds=summarize(fires_manager.fires))

def summarize(fires):
    if not fires:
        return []

    # TODO: summarize per active_area?  per activity collection
    area_by_fccs_id = defaultdict(lambda: 0)
    total_area = 0
    for fire in fires:
        for ac in fire['activity']:
            for aa in ac.active_areas:
                total_area += aa.total_area
                for loc in aa.locations:
                    for fb in loc.get('fuelbeds', [{"fccs_id": "unknown", "pct": 100.0}]):
                        area_by_fccs_id[fb['fccs_id']] += (fb['pct'] / 100.0) * loc['area']

    summary = [{"fccs_id": fccs_id, "pct": (area / total_area) * 100.0}
        for fccs_id, area in area_by_fccs_id.items()]
    return sorted(summary, key=lambda a: a["fccs_id"])

# TODO: change 'get_*' functions to 'set_*' and chnge fire in place
# rather than return values ???

# According to https://en.wikipedia.org/wiki/Acre, an acre is 4046.8564224 m^2
ACRES_PER_SQUARE_METER = 1 / 4046.8564224  # == 0.0002471053814671653

class Estimator():

    def __init__(self, lookup):
        self.lookup = lookup

    def estimate(self, loc):
        """Estimates fuelbed composition based on lat/lng or perimeter
        """
        if not loc:
            raise ValueError("Insufficient data for looking up fuelbed information")

        elif loc.get('geometry'):
            geo_data = loc['geometry']
            fuelbed_info = self.lookup.look_up(geo_data)

            # If loc['area'] is defined, then we want to keep it. We're dealing
            # with a perimeter which may not be all burning.  If it isn't
            # defined, then set loc['area'] to fuelbed_info['area']
            if not loc.get('area') and fuelbed_info and fuelbed_info.get('area'):
                # fuelbed_info['area'] is in m^2
                loc['area'] = fuelbed_info['area'] * ACRES_PER_SQUARE_METER

        elif loc.get('lat') and loc.get('lng'):
            geo_data = {
                "type": "Point",
                "coordinates": [
                    loc['lng'],
                    loc['lat']
                ]
            }
            logging.debug("Converted lat,lng to geojson: %s", geo_data)
            fuelbed_info = self.lookup.look_up(geo_data)

        else:
            raise ValueError("Insufficient data for looking up fuelbed information")

        if not fuelbed_info or not fuelbed_info.get('fuelbeds'):
            # TODO: option to ignore failures ?
            raise RuntimeError("Failed to lookup fuelbed information")
        elif Config().get('fuelbeds', 'total_pct_threshold') < abs(100.0 - sum(
                [d['percent'] for d in fuelbed_info['fuelbeds'].values()])):
            raise RuntimeError("Fuelbed percentages don't add up to 100% - {fuelbeds}".format(
                fuelbeds=fuelbed_info['fuelbeds']))

        fuelbeds = [{'fccs_id':f, 'pct':d['percent']}
            for f,d in fuelbed_info['fuelbeds'].items()]

        loc.update(fuelbeds=fuelbeds)
