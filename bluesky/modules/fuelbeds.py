"""bluesky.modules.fuelbeds
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import random

__all__ = [
    'run'
]

def run(fires):
    logging.info("Running fuelbeds module")
    for fire in fires:
        Estimator(fire).estimate()


# TODO: change 'get_*' functions to 'set_*' and chnge fire in place
# rather than return values ???

class Estimator(object):

    def __init__(self, fire):
        self.fire = fire

    def estimate(self):
        if self.fire.get('shape_file'):
            # TODO: import
            raise NotImplementedError("Importing of shape data from file not implemented")

        if self.fire.get('shape'):
            self._set_from_shape()
        elif self.fire.get('latitude') and self.fire.get('longitude') and self.fire.get('area'):
            self._set_fuelbeds_from_lat_lng()
        else:
            raise RuntimeError("Insufficient data for looking up fuelbed information")

        self._truncate()

    def _set_from_shape(self):
        # TODO: replace this dummy code with code that looks up fccs ids
        # with percentages from data stored in self.fire.shape
        fire_id = self.fire.get('id', "FAKEID") # every fire should have an id
        random.seed(ord(fire_id[0]))
        self.fire.fuelbeds = []
        num_fires = random.randint(3,6)
        remaining_pct = 100
        for i in xrange(num_fires):
            p = random.randint(0, remaining_pct-(num_fires-i)) if i != num_fires else remaining_pct
            self.fire.fuelbeds.append({
                'fccs_id': random.randint(1, 29),  # note: this could results in dupes
                'pct': p
            })
            remaining_pct -= self.fire.fuelbeds[-1]['pct']


    def _set_fuelbeds_from_lat_lng(self):
        # TODO: replace this dummy code with code that lookgs up fccs id(s)
        # from the fire's lat/lng + area
        fire_id = self.fire.get('id', "FAKEID") # every fire should have an id
        random.seed(ord(fire_id[0]))
        self.fire.fuelbeds = [{
            'fccs_id': ord(fire_id[0]) % 29 + 1,
            'pct': 100
        }]

    TRUNCATION_PERCENTAGE_THRESHOLD = 10
    def _truncate(self):
        """Sorts fuelbeds by decreasing percentage, and

        Sort fuelbeds by decreasing percentage, and then use all
        fuelbeds up to 90% coverage (make that configurable, but default to
        90%), and then adjust percentages of included fires so that total is 100%.
        ex. if 3 fires, 85%, 8%, and 7%, use only the first and second, and then
          85% -> 85% * 100 / (100 - 7) = 91.4%
          8% -> 7% * 100 / (100 - 7) = 8.6%
        """
        if self.fire.fuelbeds:
            self.fire.fuelbeds.sort(key=lambda fb: fb['pct'])
            self.fire.fuelbeds.reverse()
            total_pct = 0
            while total_pct + self.fire.fuelbeds[-1]['pct'] < self.TRUNCATION_PERCENTAGE_THRESHOLD:
                total_pct += self.fire.fuelbeds.pop()['pct']
