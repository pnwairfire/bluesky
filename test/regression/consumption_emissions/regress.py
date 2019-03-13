#!/usr/bin/env python

__author__ = "Joel Dubowy"

import copy
import csv
import glob
import logging
import os
import subprocess
import sys
import traceback
import uuid

import afscripting

# Hack to put the repo root dir at the front of sys.path so that
# the local bluesky package is found
# app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
#    os.path.abspath(__file__)))))
# sys.path.insert(0, app_root)

# We're running bluesky via the package rather than by running the bsp script
# to allow breaking into the code (with pdb)
from bluesky import models
from bluesky.config import Config

# TODO: rename this script

# TODO: use a regression testing framework?

DATA_DIRS = [ os.path.basename(d.rstrip('/'))
    for d in glob.glob(os.path.join(os.path.dirname(__file__), 'data/*'))]

REQUIRED_ARGS = [
    {
        'short': '-d',
        'long': '--data-dir',
        'help': 'options "{}"'.format(" or ".join(DATA_DIRS))
    }
]

OPTIONAL_ARGS = [
    {
        'short': '-i',
        'long': '--scenario-id',
        'help': 'to run just one of the scenarios'
    },
    {
        'short': '-e',
        'long': '--emissions-model',
        'help': '"feps", "prichard-oneill", or "consume"; default "consume"',
        'default': 'consume'
    },
    {
        'long': '--include-emissions-details',
        'help': 'compare emissions details values',
        'default': False,
        'action': 'store_true'
    }
]

EXAMPLES_STR = """
"""

BASE_FIRE = {
    "event_of": {
        "name": "regression test fire",
        "fuel_type": "natural"
        # "id" to be filled in
    },
    'growth': [{
        "fuelbeds": [{
            # "fccs_id" to be filled in
            # "pct" to be filled in
        }],
        "location": {
            "latitude": 47.4316976,
            "longitude": -121.3990506,
            "utc_offset": "-09:00"
        }
    }]
}


def load_csv(filename):
    data = []
    with open(filename) as f:
        return [r for r in csv.DictReader(f)]

def load_scenario(input_filename):
    """Loads scenario input file and instantiates a fires_manager object
    to run bsp.

    Note that we have various options:
     - create one fire with one growth window and N fuelbeds, or
     - create one fire with N growth windows, each with 1 fuelbed, or
     - create N fires ,each with growth window, and each growth
       window with with 1 fuelbed
     - any other combination of fires, growth windows, and fuelbeds
       that result in N total growth windows

    Either should work, assuming the ecoregion is the same for each row
    in the scenario (which is currently the case).  In case this changes
    and the assumption is broken, we'll go with creating N fires.
    """
    fires_manager = models.fires.FiresManager()
    rows = load_csv(input_filename)
    # compute total_area and use it to compute fuelbed pct *only it*
    # we switch to having one fire with N fuelbeds (instead of
    # N fires with 1 fuelbed each, which we're currently using)
    #total_area = sum([int(r['area']) for r in rows])
    for row_dict in rows:
        fire = models.fires.Fire(copy.deepcopy(BASE_FIRE))
        fire.event_of["id"] = str(uuid.uuid1())
        area = int(row_dict['area'])
        fire.growth[0]['location']['area'] = area
        fire.growth[0]['location']['ecoregion'] = row_dict['ecoregion']
        fire.growth[0]['location']['fuel_moisture_duff_pct'] = int(row_dict['fm_duff'])
        fire.growth[0]['location']['fuel_moisture_1000hr_pct'] = int(row_dict['fm_1000hr'])
        fire.growth[0]['location']['canopy_consumption_pct'] = int(row_dict['can_con_pct'])
        fire.growth[0]['location']['shrub_blackened_pct'] = int(row_dict['shrub_black_pct'])
        fire.growth[0]['location']['pile_blackened_pct'] = int(row_dict['pile_black_pct'])
        fire.growth[0]['location']['output_units'] = row_dict['units']
        fire.growth[0]['fuelbeds'][0]['fccs_id'] = row_dict['fuelbeds']
        # See note above about 1 fire + N fuelbeds vs N fires + 1 fuelbed each
        #fire.growth[0]['fuelbeds'][0]['pct'] = float(area) / float(total_area)
        fire.growth[0]['fuelbeds'][0]['pct'] = 100.0
        fires_manager.add_fire(fire)
    return fires_manager

PHASE_TRANSLATIONS = {
    "Flame": "flaming",
    "Smold": "smoldering",
    "Resid": "residual"
}
CONSUMPTION_OUTPUT_HEADER_TRANSLATIONS = {
    #"Fuelbeds": [],
    # ignore "Filename"
    "Total Consumption": ["summary", "total", "total"],
    "Canopy Consumption": ["summary", "canopy", "total"],
    "Shrub Consumption": ["summary", "shrub", "total"],
    "Herb Consumption": ["summary", "nonwoody", "total"],
    "Wood Consumption": ["summary", "woody fuels", "total"],
    "LLM Consumption": ["summary", "litter-lichen-moss", "total"],
    "Ground Consumption": ["summary", "ground fuels", "total"],
    "C_total_F": ["summary", "total", "flaming"],
    "C_canopy_F": ["summary", "canopy", "flaming"],
    "C_shrub_F": ["summary", "shrub", "flaming"],
    "C_herb_F": ["summary", "nonwoody", "flaming"],
    "C_wood_F": ["summary", "woody fuels", "flaming"],
    "C_llm_F": ["summary", "litter-lichen-moss", "flaming"],
    "C_ground_F": ["summary", "ground fuels", "flaming"],
    "C_total_S": ["summary", "total", "smoldering"],
    "C_canopy_S": ["summary", "canopy", "smoldering"],
    "C_shrub_S": ["summary", "shrub", "smoldering"],
    "C_herb_S": ["summary", "nonwoody", "smoldering"],
    "C_wood_S": ["summary", "woody fuels", "smoldering"],
    "C_llm_S": ["summary", "litter-lichen-moss", "smoldering"],
    "C_ground_S": ["summary", "ground fuels", "smoldering"],
    "C_total_R": ["summary", "total", "residual"],
    "C_canopy_R": ["summary", "canopy", "residual"],
    "C_wood_R": ["summary", "woody fuels", "residual"],
    "C_llm_R": ["summary", "litter-lichen-moss", "residual"],
    "C_ground_R": ["summary", "ground fuels", "residual"],
    "C_overstory_crown": ["canopy", "overstory", "total"],
    "C_midstory_crown": ["canopy", "midstory", "total"],
    "C_understory_crown": ["canopy", "understory", "total"],
    "C_snagC1F_crown": ["canopy", "snags class 1 foliage", "total"],
    "C_snagC1F_wood": ["canopy", "snags class 1 no foliage", "total"],
    "C_snagC1_wood": ["canopy", "snags class 1 wood", "total"],
    "C_snagC2_wood": ["canopy", "snags class 2", "total"],
    "C_snagC3_wood": ["canopy", "snags class 3", "total"],
    "C_ladder": ["canopy", "ladder fuels", "total"],
    "C_shrub_1live": ["shrub", "primary dead", "total"],
    "C_shrub_1dead": ["shrub", "primary live", "total"],
    "C_shrub_2live": ["shrub", "secondary dead", "total"],
    "C_shrub_2dead": ["shrub", "secondary live", "total"],
    "C_herb_1live": ["nonwoody", "primary dead", "total"],
    "C_herb_1dead": ["nonwoody", "primary live", "total"],
    "C_herb_2live": ["nonwoody", "secondary dead", "total"],
    "C_herb_2dead": ["nonwoody", "secondary live", "total"],
    "C_wood_1hr": ["woody fuels", "1-hr fuels", "total"],
    "C_wood_10hr": ["woody fuels", "10-hr fuels", "total"],
    "C_wood_100hr": ["woody fuels", "100-hr fuels", "total"],
    "C_wood_S1000hr": ["woody fuels", "1000-hr fuels sound", "total"],
    "C_wood_R1000hr": ["woody fuels", "1000-hr fuels rotten", "total"],
    "C_wood_S10khr": ["woody fuels", "10000-hr fuels sound", "total"],
    "C_wood_R10khr": ["woody fuels", "10000-hr fuels rotten", "total"],
    "C_wood_S+10khr": ["woody fuels", "10k+-hr fuels sound", "total"],
    "C_wood_R+10khr": ["woody fuels", "10k+-hr fuels rotten", "total"],
    "C_stump_sound": ["woody fuels", "stumps sound", "total"],
    "C_stump_rotten": ["woody fuels", "stumps rotten", "total"],
    "C_stump_lightered": ["woody fuels", "stumps lightered", "total"],
    "C_litter": ["litter-lichen-moss", "litter", "total"],
    "C_lichen": ["litter-lichen-moss", "lichen", "total"],
    "C_moss": ["litter-lichen-moss", "moss", "total"],
    "C_upperduff": ["ground fuels", "duff upper", "total"],
    "C_lowerduff": ["ground fuels", "duff lower", "total"],
    "C_basal_accum": ["ground fuels", "basal accumulations", "total"],
    "C_squirrel": ["ground fuels", "squirrel middens", "total"]
}
EMISSIONS_OUTPUT_HEADER_TRANSLATIONS = {
    "CH4 Emissions": ["total", "CH4"],
    "CO Emissions": ["total", "CO"],
    "CO2 Emissions": ["total", "CO2"],
    "NMHC Emissions": ["total", "NMHC"],
    "PM Emissions": ["total", "PM"],
    "PM10 Emissions": ["total", "PM10"],
    "PM25 Emissions": ["total", "PM2.5"],
    "E_ch4_F": ["flaming", "CH4"],
    "E_co_F": ["flaming", "CO"],
    "E_co2_F": ["flaming", "CO2"],
    "E_nmhc_F": ["flaming", "NMHC"],
    "E_pm_F": ["flaming", "PM"],
    "E_pm10_F": ["flaming", "PM10"],
    "E_pm25_F": ["flaming", "PM2.5"],
    "E_ch4_S": ["smoldering", "CH4"],
    "E_co_S": ["smoldering", "CO"],
    "E_co2_S": ["smoldering", "CO2"],
    "E_nmhc_S": ["smoldering", "NMHC"],
    "E_pm_S": ["smoldering", "PM"],
    "E_pm10_S": ["smoldering", "PM10"],
    "E_pm25_S": ["smoldering", "PM2.5"],
    "E_ch4_R": ["residual", "CH4"],
    "E_co_R": ["residual", "CO"],
    "E_co2_R": ["residual", "CO2"],
    "E_nmhc_R": ["residual", "NMHC"],
    "E_pm_R": ["residual", "PM"],
    "E_pm10_R": ["residual", "PM10"],
    "E_pm25_R": ["residual", "PM2.5"]
}
EMISSIONS_DETAILS_OUTPUT_HEADER_TRANSLATIONS = {
    "CH4_canopy": ["summary", "canopy", "total", "CH4"],
    "CH4_shrub": ["summary", "shrub", "total", "CH4"],
    "CH4_herb": ["summary", "nonwoody", "total", "CH4"],
    "CH4_wood": ["summary", "woody fuels", "total", "CH4"],
    "CH4_llm": ["summary", "litter-lichen-moss", "total", "CH4"],
    "CH4_ground": ["summary", "ground fuels", "total", "CH4"],
    "CO_canopy": ["summary", "canopy", "total", "CO"],
    "CO_shrub": ["summary", "shrub", "total", "CO"],
    "CO_herb": ["summary", "nonwoody", "total", "CO"],
    "CO_wood": ["summary", "woody fuels", "total", "CO"],
    "CO_llm": ["summary", "litter-lichen-moss", "total", "CO"],
    "CO_ground": ["summary", "ground fuels", "total", "CO"],
    "CO2_canopy": ["summary", "canopy", "total", "CO2"],
    "CO2_shrub": ["summary", "shrub", "total", "CO2"],
    "CO2_herb": ["summary", "nonwoody", "total", "CO2"],
    "CO2_wood": ["summary", "woody fuels", "total", "CO2"],
    "CO2_llm": ["summary", "litter-lichen-moss", "total", "CO2"],
    "CO2_ground": ["summary", "ground fuels", "total", "CO2"],
    "NMHC_canopy": ["summary", "canopy", "total", "NMHC"],
    "NMHC_shrub": ["summary", "shrub", "total", "NMHC"],
    "NMHC_herb": ["summary", "nonwoody", "total", "NMHC"],
    "NMHC_wood": ["summary", "woody fuels", "total", "NMHC"],
    "NMHC_llm": ["summary", "litter-lichen-moss", "total", "NMHC"],
    "NMHC_ground": ["summary", "ground fuels", "total", "NMHC"],
    "PM_canopy": ["summary", "canopy", "total", "PM"],
    "PM_shrub": ["summary", "shrub", "total", "PM"],
    "PM_herb": ["summary", "nonwoody", "total", "PM"],
    "PM_wood": ["summary", "woody fuels", "total", "PM"],
    "PM_llm": ["summary", "litter-lichen-moss", "total", "PM"],
    "PM_ground": ["summary", "ground fuels", "total", "PM"],
    "PM10_canopy": ["summary", "canopy", "total", "PM10"],
    "PM10_shrub": ["summary", "shrub", "total", "PM10"],
    "PM10_herb": ["summary", "nonwoody", "total", "PM10"],
    "PM10_wood": ["summary", "woody fuels", "total", "PM10"],
    "PM10_llm": ["summary", "litter-lichen-moss", "total", "PM10"],
    "PM10_ground": ["summary", "ground fuels", "total", "PM10"],
    "PM25_canopy": ["summary", "canopy", "total", "PM2.5"],
    "PM25_shrub": ["summary", "shrub", "total", "PM2.5"],
    "PM25_herb": ["summary", "nonwoody", "total", "PM2.5"],
    "PM25_wood": ["summary", "woody fuels", "total", "PM2.5"],
    "PM25_llm": ["summary", "litter-lichen-moss", "total", "PM2.5"],
    "PM25_ground": ["summary", "ground fuels", "total", "PM2.5"]
}
HEAT_OUTPUT_HEADER_TRANSLATIONS = {
    "Total Heat Release": "total",
    "Flaming Heat Release": "flaming",
    "Smoldering Heat Release": "smoldering",
    "Residual Heat Release": "residual"
}
def load_output(input_filename):
    # Consumption + emissions by fuelbed and fuel category
    consumption_output_filename = input_filename.replace('.csv', '_out.csv')
    expected_partials = {}
    for r in load_csv(consumption_output_filename):
        fb_c = {}
        fb_h = {}
        fb_e = {}
        fb_ed = {}
        for k in r:
            if k in CONSUMPTION_OUTPUT_HEADER_TRANSLATIONS:
                c, sc, p = CONSUMPTION_OUTPUT_HEADER_TRANSLATIONS[k]
                fb_c[c] = fb_c.get(c, {})
                fb_c[c][sc] = fb_c[c].get(sc, {})
                fb_c[c][sc][p] = [float(r[k])]
            elif k in HEAT_OUTPUT_HEADER_TRANSLATIONS:
                p = HEAT_OUTPUT_HEADER_TRANSLATIONS[k]
                fb_h[p] = [float(r[k])]
            elif k in EMISSIONS_OUTPUT_HEADER_TRANSLATIONS:
                p, s = EMISSIONS_OUTPUT_HEADER_TRANSLATIONS[k]
                fb_e[p] = fb_e.get(p, {})
                fb_e[p][s] = [float(r[k])]
            elif k in EMISSIONS_DETAILS_OUTPUT_HEADER_TRANSLATIONS:
                a, b, c, d = EMISSIONS_DETAILS_OUTPUT_HEADER_TRANSLATIONS[k]
                fb_ed[a] = fb_ed.get(a, {})
                fb_ed[a][b] = fb_ed[a].get(b, {})
                fb_ed[a][b][c] = fb_ed[a][b].get(c, {})
                fb_ed[a][b][c][d] = [float(r[k])]

        fccs_id = r['Fuelbeds']
        expected_partials[fccs_id] = {
            'consumption': fb_c,
            'heat': fb_h,
            'emissions': fb_e,
            'emissions_details': fb_ed
        }

    # total Emissions
    input_dir, input_filename = os.path.split(input_filename)
    emissions_output_filename = os.path.join(input_dir,
        "feps_input_em_{}".format(input_filename))
    expected_totals =  {
        'emissions': {}
    }
    for r in load_csv(emissions_output_filename):
        p = PHASE_TRANSLATIONS[r.pop('Phase')]
        expected_totals['emissions'][p] = {
            k.upper(): [float(v)] for k, v in r.items()
        }

    return expected_partials, expected_totals

def check_value(counts, counts_key, actual, expected, *keys):
    for k in keys[:-1]:
        actual = actual.get(k, {})
        expected = expected.get(k, {})
    valid_comparison = keys[-1] in actual and keys[-1] in expected
    actual = actual.get(keys[-1], '???')
    expected = expected.get(keys[-1], '???')
    # TODO: check equality with allowable difference instead of just '=='
    log_args = ("%s - %s: actual vs. expected (%s): %s vs %s", counts_key.upper(),
        keys[0].upper(), ', '.join(keys[1:]), actual, expected)
    if valid_comparison:
        match = actual == expected
        counts[counts_key][keys[0]]['total'] += 1
        counts[counts_key][keys[0]]['matches'] += int(match)
        (logging.debug if match else logging.error)(*log_args)
    else:
        logging.debug(*log_args)

def check(actual, expected_partials, expected_totals):

    # TODO: multiply expected by area ???
    #   (I'm seeing values like:
    #     2016-01-17 06:56:28,054 DEBUG: actual vs. expected (flaming, pm25):  [27743.094436046558] vs [14.491]
    #     2016-01-17 06:56:28,054 DEBUG: actual vs. expected (residual, co2):  [14269215.486186512] vs [3926.008]
    #     2016-01-17 06:56:28,054 DEBUG: actual vs. expected (residual, co):  [1335240.064130065] vs [360.048]
    #     2016-01-17 06:56:28,054 DEBUG: actual vs. expected (residual, pm10):  [160496.519555684] vs [44.202]
    #     2016-01-17 06:56:28,055 DEBUG: actual vs. expected (residual, nmhc):  [46592.137014784814] vs [12.542]
    #   )
    #  Also play around with other pending changes to see how they affect values
    #  (like tons vs tons_ac, rerunnig consumption vs not doing so, etc..)

    counts = {
        "partials": {k: {'matches': 0, 'total': 0} for k in [
            'consumption', 'heat', 'emissions', 'emissions_details']},
        "totals": {k: {'matches': 0, 'total': 0} for k in ['emissions']}
    }

    for fire in actual['fire_information']:
        fb = fire['growth'][0]['fuelbeds'][0]
        fccs_id = fb['fccs_id']
        fb_e = expected_partials[fccs_id]

        for c in  fb_e['consumption']:
            for s in  fb_e['consumption'][c]:
                #logging.debug('{} {}'.format (c, s))
                for p in  fb_e['consumption'][c][s]:
                    check_value(counts, 'partials', fb, fb_e, 'consumption', c, s, p)

        for p in fb_e['heat']:
            check_value(counts, 'partials', fb, fb_e, 'heat', p)

        for p in fb_e['emissions']:
            for s in fb_e['emissions'][p]:
                check_value(counts, 'partials', fb, fb_e, 'emissions', p, s)

        if 'emissions_details' in fb:
            for a in  fb_e['emissions_details']:
                for b in  fb_e['emissions_details'][a]:
                    for c in  fb_e['emissions_details'][a][b]:
                        for d in  fb_e['emissions_details'][a][b][c]:
                            check_value(counts, 'partials', fb, fb_e, 'emissions_details', a, b, c, d)

    for phase in expected_totals['emissions']:
        for species in expected_totals['emissions'][phase]:
            check_value(counts, 'totals', actual['summary'], expected_totals,
                'emissions', phase, species)

    success = True
    logging.info('Final counts')
    for k in counts:
        logging.info('  %s:', k.upper())
        for l in counts[k]:
            logging.info('    %s: %s out of %s correct - %s', l.upper(),
                counts[k][l]['matches'], counts[k][l]['total'],
                'PASS' if counts[k][l]['matches'] == counts[k][l]['total'] else 'FAIL')
            success = success and counts[k][l]['matches'] == counts[k][l]['total']
    return success

def run(args):
    pattern = '{}/data/{}/scen_{}.csv'.format(
        os.path.abspath(os.path.dirname(__file__)),
        args.data_dir, args.scenario_id or '[0-9]')
    input_filenames = glob.glob(pattern)
    if not input_filenames:
        logging.error("No matching scnarios")
        sys.exit(1)
    logging.info("Scanarios: {}".format(', '.join(
        [os.path.basename(n) for n in input_filenames])))

    success = True
    for input_filename in input_filenames:
        fires_manager = load_scenario(input_filename)
        Config.set(args.emissions_model, 'emissions', 'model')
        Config.set(args.include_emissions_details,
            'emissions','include_emissions_details')
        fires_manager.modules = ['consumption', 'emissions']
        fires_manager.run()
        actual = fires_manager.dump()
        expected_partials, expected_totals = load_output(
            input_filename)
        success = success and check(actual, expected_partials, expected_totals)
    return success

if __name__ == "__main__":
    parser, args = afscripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)
    if args.data_dir not in DATA_DIRS:
        logging.error("Invalid data directory: %s", args.data_dir)
        sys.exit(1)

    try:
        success = run(args)

    except Exception as e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        afscripting.utils.exit_with_msg(e)

    sys.exit(int(not success))