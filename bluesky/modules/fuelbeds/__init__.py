"""bluesky.modules.fuelbeds
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import random

def run(fires):
    logging.info("Running fuelbeds module")
    for fire in fires:
        set_fuelbeds(fire)

def set_fuelbeds(fire):
    if fire.get('shape_file'):
        # TODO: import
        raise NotImplementedError("Importing of shape data from file not implemented")

    if fire.get('shape'):
        fire.fuelbeds = get_fuelbeds_from_shape(fire)
    elif fire.get('latitude') and fire.get('longitude') and fire.get('area'):
        fire.fuelbeds = get_fuelbeds_from_lat_lng(fire)
    else:
        raise RuntimeError("Insufficient data for looking up fuelbed information")

    truncate(fire.fuelbeds)

def get_fuelbeds_from_shape(fire):
    # TODO: replace this dummy code with code that looks up fccs ids
    # with percentages from data stored in fire.shape
    fire_id = fire.get('id', "FAKEID") # every fire should have an id
    random.seed(ord(fire_id[0]))
    fuelbeds = []
    num_fires = random.randint(3,6)
    remaining_percentage = 100
    for i in xrange(num_fires):
        p = random.randint(0, remaining_percentage-(num_fires-i)) if i != num_fires else remaining_percentage
        fuelbeds.append({
            'fccs_id': random.randint(0, 99),  # note: this could results in dupes
            'percentage': p
        })
        remaining_percentage -= fuelbeds[-1]['percentage']
    return fuelbeds


def get_fuelbeds_from_lat_lng(fire):
    # TODO: replace this dummy code with code that lookgs up fccs id(s)
    # from fire.lat/fire.lng + fire.area
    fire_id = fire.get('id', "FAKEID") # every fire should have an id
    random.seed(ord(fire_id[0]))
    fuelbeds = [{
        'fccs_id': ord(fire_id[0]) % 99 + 1,
        'percentage': 100
    }]
    return fuelbeds

def truncate(fuelbeds):
    # TODO: sort fuelbeds by decreasing percentage, and then use all
    # fuelbeds up to 90% coverage (make that configurable, but default to
    # 90%), and then adjust percentages of included fires so that total is 100%.
    # ex. if 3 fires, 85%, 8%, and 7%, use only the first and second, and then
    #   85% -> 85% * 100 / (100 - 7) = 91.4%
    #   8% -> 7% * 100 / (100 - 7) = 8.6%
    pass