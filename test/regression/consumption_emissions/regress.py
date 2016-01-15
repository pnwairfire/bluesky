#!/usr/bin/env python

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2015, AirFire, PNW, USFS"

import copy
import csv
import glob
import logging
import os
import subprocess
import sys
import traceback
import uuid

from pyairfire import scripting

# Hack to put the repo root dir at the front of sys.path so that
# the local bluesky package is found
# app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
#    os.path.abspath(__file__)))))
# sys.path.insert(0, app_root)

# We're running bluesky via the package rather than by running the bsp script
# to allow breaking into the code (with pdb)
from bluesky import models

# TODO: rename this script

# TODO: use a regression testing framework?

REQUIRED_ARGS = [
]

OPTIONAL_ARGS = [
]

EXAMPLES_STR = """
"""

BASE_FIRE = {
    "event_of": {
        "name": "regression test fire"
        # "id" to be filled in
    },
    "fuelbeds": [{
        # "fccs_id" to be filled in
        # "pct" to be filled in
    }],
    "location": {
        "latitude": 47.4316976,
        "longitude": -121.3990506,
        "utc_offset": "-09:00"
    }
}


def load_csv(filename):
    data = []
    with open(filename) as f:
        return [r for r in csv.DictReader(f)]

def load_scenario(input_filename):
    """Loads scenario input file and instantiates a fires_manager object
    to run bsp.

    Note that we have two options:
     - create one fire with N fuelbeds, or
     - create N fires, each with 1 fuelbed

    Either should work, assuming the ecoregion is the same for each row
    in the scenario (which is currently the case).  In case this changes
    and the assumption is broken, we'll go with creating N fires.
    """
    fires_manager = models.fires.FiresManager()
    rows = load_csv(input_filename)
    total_area = sum([int(r['area']) for r in rows])
    for row_dict in rows:
        fire = models.fires.Fire(copy.deepcopy(BASE_FIRE))
        fire.event_of["id"] = str(uuid.uuid1())
        area = int(row_dict['area'])
        fire.location['area'] = area
        fire.location['ecoregion'] = row_dict['ecoregion']
        fire.location['fuel_moisture_duff_pct'] = row_dict['fm_duff']
        fire.location['fuel_moisture_1000hr_pct'] = row_dict['fm_1000hr']
        fire.location['canopy_consumption_pct'] = row_dict['can_con_pct']
        fire.location['shrub_blackened_pct'] = row_dict['shrub_black_pct']
        fire.location['pile_blackened_pct'] = row_dict['pile_black_pct']
        fire.location['output_units'] = row_dict['units']
        fire.fuelbeds[0]['fccs_id'] = row_dict['fuelbeds']
        fire.fuelbeds[0]['area'] = float(area) / float(total_area)
        fires_manager.add_fire(fire)
    return fires_manager

PHASE_TRANSLATIONS = {
    "Flame": "flaming",
    "Smold": "smoldering",
    "Resid": "residual"
}
def load_output(input_filename):
    input_dir, input_filename = os.path.split(input_filename)
    emissions_output_filename = os.path.join(input_dir,
        "feps_input_em_{}".format(input_filename))
    # TODO: also load intermediate consumption values ?
    return {r.pop('Phase'): {k: [v] for k, v in r.items()}
        for r in load_csv(emissions_output_filename)}
    # TODO: delete the following if the above works
    # expected_emissions = {}
    # for r in load_csv(emissions_output_filename):
    #     expected_emissions[r.pop('Phase')] = {k: [v] for k, v in r.items()}
    # return expected_emissions

def run(args):
    pattern = '{}/data/scen_[0-9].csv'.format(
        os.path.abspath(os.path.dirname(__file__)))
    for input_filename in glob.glob(pattern):
        fire_manager = load_scenario(input_filename)
        fire_manager.run()
        actual = fire_manager.dump()
        expected_emissions = load_output(input_filename)
        # TODO: compare expected to actual


if __name__ == "__main__":
    parser, args = scripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)

    try:
        run(args)

    except Exception, e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        scripting.utils.exit_with_msg(e)
