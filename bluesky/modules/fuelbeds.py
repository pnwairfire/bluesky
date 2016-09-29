"""bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import logging
import random
from collections import defaultdict

import fccsmap
from fccsmap.lookup import FccsLookUp
from functools import reduce

__all__ = [
    'run'
]

__version__ = "0.1.0"

FCCS_VERSION = '2' # TODO: make this configurable

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running fuelbeds module")
    fires_manager.processed(__name__, __version__,
        fccsmap_version=fccsmap.__version__)
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            if not fire.get('growth'):
                raise ValueError(
                    "Growth information required to look up fuelbeds")

            for g in fire['growth']:
                if not g.get('location'):
                    raise ValueError(
                        "growth location information required to look up fuelbeds")
                # TODO: instead of instantiating a new FccsLookUp and Estimator
                #   for each growth object, create AK and non-AK lookup and
                #   estimator objects that are reused, and set reference to
                #   correct one here
                lookup = FccsLookUp(is_alaska=g['location'].get('state')=='AK',
                    fccs_version=FCCS_VERSION)
                Estimator(lookup).estimate(g)

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

    area_by_fccs_id = defaultdict(lambda: 0)
    total_area = 0
    for fire in fires:
        for g in fire['growth']:
            total_area += g['location']['area']
            for fb in g['fuelbeds']:
                area_by_fccs_id[fb['fccs_id']] += (fb['pct'] / 100.0) * g['location']['area']
    summary = [{"fccs_id": fccs_id, "pct": (area / total_area) * 100.0}
        for fccs_id, area in area_by_fccs_id.items()]
    return sorted(summary, key=lambda a: a["fccs_id"])

# TODO: change 'get_*' functions to 'set_*' and chnge fire in place
# rather than return values ???

# According to https://en.wikipedia.org/wiki/Acre, an acre is 4046.8564224 m^2
ACRES_PER_SQUARE_METER = 1 / 4046.8564224  # == 0.0002471053814671653
# Allow summed fuel percentages to be between 99.5% and 100.5%
# TODO: Move to common constants module? (timeprofiling defines similar
# constant for total growth percentage)
TOTAL_PCT_THRESHOLD = 0.5

class Estimator(object):

    def __init__(self, lookup):
        self.lookup = lookup

    def estimate(self, growth_obj):
        """Estimates fuelbed composition based on lat/lng or GeoJSON data.

        If growth_obj['location']['geojson'] is defined, it will look something like
        the following:

            {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-84.8194, 30.5222],
                            [-84.8197, 30.5209],
                            ...
                            [-84.8193, 30.5235],
                            [-84.8194, 30.5222]
                        ]
                    ]
                ]
            }
        """
        if not growth_obj.get('location'):
            raise ValueError("Insufficient data for looking up fuelbed information")

        fuelbed_info = {}
        if growth_obj['location'].get('shape_file'):
            raise NotImplementedError("Importing of shape data from file not implemented")
        if growth_obj['location'].get('geojson'):
            fuelbed_info = self.lookup.look_up(growth_obj['location']['geojson'])
            # fuelbed_info['area'] is in m^2
            # TDOO: only use fuelbed_info['area'] if growth_obj['location']['area']
            # isn't already defined?
            if fuelbed_info and fuelbed_info.get('area'):
                growth_obj['location']['area'] = fuelbed_info['area'] * ACRES_PER_SQUARE_METER
        elif growth_obj['location'].get('latitude') and growth_obj['location'].get('longitude'):
            fuelbed_info = self.lookup.look_up_by_lat_lng(
                growth_obj['location']['latitude'], growth_obj['location']['longitude'])
        else:
            raise ValueError("Insufficient data for looking up fuelbed information")

        if not fuelbed_info or not fuelbed_info.get('fuelbeds'):
            # TODO: option to ignore failures ?
            raise RuntimeError("Failed to lookup fuelbed information")
        elif TOTAL_PCT_THRESHOLD < abs(100.0 - sum(
                [d['percent'] for d in fuelbed_info['fuelbeds'].values()])):
            raise RuntimeError("Fuelbed percentages don't add up to 100% - {fuelbeds}".format(
                fuelbeds=fuelbed_info['fuelbeds']))

        growth_obj['fuelbeds'] = [{'fccs_id':f, 'pct':d['percent']}
            for f,d in fuelbed_info['fuelbeds'].items()]

        self._truncate(growth_obj)
        self._adjust_percentages(growth_obj)

    TRUNCATION_PERCENTAGE_THRESHOLD = 10
    def _truncate(self, growth_obj):
        """Sorts fuelbeds by decreasing percentage, and

        Sort fuelbeds by decreasing percentage, and then use all
        fuelbeds up to 90% coverage (make that configurable, but default to
        90%), and then adjust percentages of included growth_objs so that total is 100%.
        ex. if 3 growth_objs, 85%, 8%, and 7%, use only the first and second, and then
          85% -> 85% * 100 / (100 - 7) = 91.4%
          8% -> 7% * 100 / (100 - 7) = 8.6%
        """
        if not growth_obj['fuelbeds']:
            return

        # TDOO: make sure percentages add up to 100%
        growth_obj['fuelbeds'].sort(key=lambda fb: fb['pct'])
        growth_obj['fuelbeds'].reverse()
        total_popped_pct = 0
        while total_popped_pct + growth_obj['fuelbeds'][-1]['pct'] < self.TRUNCATION_PERCENTAGE_THRESHOLD:
            total_popped_pct += growth_obj['fuelbeds'].pop()['pct']

    def _adjust_percentages(self, growth_obj):
        total_pct = sum([fb['pct'] for fb in growth_obj['fuelbeds']])
        for fb in growth_obj['fuelbeds']:
            fb['pct'] *= 100.0 / total_pct
