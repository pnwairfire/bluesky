"""bluesky.modules.fuelbeds
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import random

from fccsmap.lookup import FccsLookUp

__all__ = [
    'run'
]

FCCS_VERSION = '2' # TODO: make this configurable

def run(fires):
    logging.info("Running fuelbeds module")
    for fire in fires:
        # TODO: instead of instantiating a new FccsLookUp and Estimator for
        # each fire, create AK and non-AK lookup and estimator objects that
        # are reused, and set reference to correct one here
        lookup = FccsLookUp(is_alaska=fire.get('state')=='AK',
            fccs_version=FCCS_VERSION)
        Estimator(lookup).estimate(fire)


# TODO: change 'get_*' functions to 'set_*' and chnge fire in place
# rather than return values ???

# According to https://en.wikipedia.org/wiki/Acre, an acre is 4046.8564224 m^2
ACRES_PER_SQUARE_METER = 1 / 4046.8564224  # == 0.0002471053814671653

class Estimator(object):

    def __init__(self, lookup):
        self.lookup = lookup

    def estimate(self, fire):
        """Estimates fuelbed composition based on lat/lng or perimeter vector
        data.

        If fire['perimeter'] is defined, it will look something like the
        following:

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
        fuelbed_info = {}
        if fire.get('shape_file'):
            raise NotImplementedError("Importing of shape data from file not implemented")
        if fire.get('perimeter'):
            fuelbed_info = self.lookup.look_up(fire['perimeter'])
            # fuelbed_info['area'] is in m^2
            # TDOO: only use fuelbed_info['area'] is in m^2 if fire.area
            # isn't already defined?
            fire.area = fuelbed_info['area'] * ACRES_PER_SQUARE_METER
        elif fire.get('latitude') and fire.get('longitude'):
            fuelbed_info = self.lookup.look_up_by_lat_lng(fire['latitude'],
                fire['longitude'])
        else:
            raise RuntimeError("Insufficient data for looking up fuelbed information")

        if not fuelbed_info:
            # TODO: option to ignore failures ?
            raise RuntimeError("Failed to lookup fuelbed information")

        fire.fuelbeds = [{'fccs_id':f, 'pct':d['percent']}
            for f,d in fuelbed_info['fuelbeds'].items()]

        self._truncate(fire)
        self._adjust_percentages(fire)

    TRUNCATION_PERCENTAGE_THRESHOLD = 10
    def _truncate(self, fire):
        """Sorts fuelbeds by decreasing percentage, and

        Sort fuelbeds by decreasing percentage, and then use all
        fuelbeds up to 90% coverage (make that configurable, but default to
        90%), and then adjust percentages of included fires so that total is 100%.
        ex. if 3 fires, 85%, 8%, and 7%, use only the first and second, and then
          85% -> 85% * 100 / (100 - 7) = 91.4%
          8% -> 7% * 100 / (100 - 7) = 8.6%
        """
        # TDOO: make sure percentages add up to 100%
        fire.fuelbeds.sort(key=lambda fb: fb['pct'])
        fire.fuelbeds.reverse()
        total_popped_pct = 0
        while total_popped_pct + fire.fuelbeds[-1]['pct'] < self.TRUNCATION_PERCENTAGE_THRESHOLD:
            total_popped_pct += fire.fuelbeds.pop()['pct']

    def _adjust_percentages(self, fire):
        total_pct = sum([fb['pct'] for fb in fire.fuelbeds])
        for fb in fire.fuelbeds:
            fb['pct'] *= 100.0 / total_pct
