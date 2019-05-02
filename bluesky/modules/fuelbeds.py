"""bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import logging
import random
from collections import defaultdict

import fccsmap
from fccsmap.lookup import FccsLookUp
from functools import reduce

from bluesky.config import Config

__all__ = [
    'run'
]

__version__ = "0.1.0"

# TODO: set is_alaska based on lat & lng instead from 'state'
FCCS_LOOKUPS = defaultdict(
    lambda: FccsLookUp(is_alaska=False, **Config.get('fuelbeds')),
    AK=FccsLookUp(is_alaska=True, **Config.get('fuelbeds'))
)

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    logging.info("Running fuelbeds module")
    fires_manager.processed(__name__, __version__,
        fccsmap_version=fccsmap.__version__)

    logging.debug('Using FCCS version %s',
        Config.get('fuelbeds', 'fccs_version'))

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for aa in fire.active_areas:
                lookup = FCCS_LOOKUPS[aa.get('state')]

                # Note that aa.locations validates that each location object
                # has either lat+lng+area or polygon
                for loc in aa.locations:
                    Estimator(lookup).estimate(loc)

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
            for aa in ac.get('active_areas'):
                total_area += aa.total_area
                for loc in aa.locations:
                    for fb in loc['fuelbeds']:
                        area_by_fccs_id[fb['fccs_id']] += (fb['pct'] / 100.0) * loc['area']

    summary = [{"fccs_id": fccs_id, "pct": (area / total_area) * 100.0}
        for fccs_id, area in area_by_fccs_id.items()]
    return sorted(summary, key=lambda a: a["fccs_id"])

# TODO: change 'get_*' functions to 'set_*' and chnge fire in place
# rather than return values ???

# According to https://en.wikipedia.org/wiki/Acre, an acre is 4046.8564224 m^2
ACRES_PER_SQUARE_METER = 1 / 4046.8564224  # == 0.0002471053814671653

class Estimator(object):

    def __init__(self, lookup):
        self.lookup = lookup

        # Is this necessary?
        for attr, val in Config.get('fuelbeds').items():
            if attr.startswith('truncation_'):
                setattr(self, attr.replace('truncation_', ''), val)

    def estimate(self, loc):
        """Estimates fuelbed composition based on lat/lng or polygon
        """
        if not loc:
            raise ValueError("Insufficient data for looking up fuelbed information")

        elif loc.get('polygon'):
            geo_data =  {
                "type": "Polygon",
                "coordinates": loc['polygon']
            }
            logging.debug("Converted polygon to geojson: %s", geo_data)
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
        elif Config.get('fuelbeds', 'total_pct_threshold') < abs(100.0 - sum(
                [d['percent'] for d in fuelbed_info['fuelbeds'].values()])):
            raise RuntimeError("Fuelbed percentages don't add up to 100% - {fuelbeds}".format(
                fuelbeds=fuelbed_info['fuelbeds']))

        fuelbeds = [{'fccs_id':f, 'pct':d['percent']}
            for f,d in fuelbed_info['fuelbeds'].items()]

        loc.update(**self._truncate(fuelbeds))

    def _truncate(self, fuelbeds):
        """Sorts fuelbeds by decreasing percentage, and

        Sort fuelbeds by decreasing percentage, use first N fuelbeds that
        reach 90% coverage or 5 count (defaults, both configurable), and
        then adjust percentages of included location so that total is 100%.
        e.g. if 3 fuelbeds, 85%, 8%, and 7%, use only the first and second,
        and then adjust percentages as follows:
          85% -> 85% * 100 / (100 - 7) = 91.4%
          8% -> 7% * 100 / (100 - 7) = 8.6%
        """
        truncated_fuelbeds = []
        total_pct = 0.0
        # iterate through fuelbeds sorted by pct (decreasing) and then by
        # fccs_id (for deterministic results in the case of equal percentages)
        for i, f in enumerate(sorted(fuelbeds, key=lambda fb: (-fb['pct'], fb['fccs_id']) )):
            truncated_fuelbeds.append(f)
            total_pct += f['pct']

            # if either treshold is None or 0, then don't truncate
            # by that that criterion
            if ((self.percentage_threshold and total_pct >= self.percentage_threshold)
                    or (self.count_threshold and i+1 >= self.count_threshold)):
                break

        # Note: we'll run adjust percentages even if nothing was truncated
        # in case percentages of initial set of fuelbeds don't add up to 100
        # (which should really never happen)

        return {
            "fuelbeds": self._adjust_percentages(truncated_fuelbeds),
            "fuelbeds_total_accounted_for_pct": total_pct
        }

    def _adjust_percentages(self, fuelbeds):
        total_pct = sum([fb['pct'] for fb in fuelbeds])

        if total_pct != 100.0:
            for fb in fuelbeds:
                # divide by total_pct before multiplying by 100 to avoid
                # rounding errors
                fb['pct'] = (fb['pct'] / total_pct) * 100.0
        # else, no adjustment necessary

        # return for convenience
        return fuelbeds
