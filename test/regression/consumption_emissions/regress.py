#!/usr/bin/env python3

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
        fire.event_of["id"] = str(uuid.uuid4())
        area = int(row_dict['area'])
        fire.growth[0]['location']['area'] = area
        fire.growth[0]['location']['ecoregion'] = row_dict['ecoregion']
        # season is deterimined in pipeline consume code by growth start date,
        # so, reverse engineer start date based on season in input file
        if row_dict['season'] == 'spring':
            fire.growth[0]['start'] = '2019-04-01'
        elif row_dict['season'] == 'summer':
            fire.growth[0]['start'] = '2019-07-01'
        elif row_dict['season'] == 'fall':
            fire.growth[0]['start'] = '2019-10-01'
        else:
            fire.growth[0]['start'] = '2019-01-01'
        fire.growth[0]['location']['fuel_moisture_duff_pct'] = int(row_dict['fm_duff'])
        fire.growth[0]['location']['fuel_moisture_litter_pct'] = int(row_dict['fm_litter'])
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
    "c_total": ["summary", "total", "total"],
    "c_canopy": ["summary", "canopy", "total"],
    "c_shrub": ["summary", "shrub", "total"],
    "c_herb": ["summary", "nonwoody", "total"],
    "c_wood": ["summary", "woody fuels", "total"],
    "c_llm": ["summary", "litter-lichen-moss", "total"],
    "c_ground": ["summary", "ground fuels", "total"],
    "c_total_F": ["summary", "total", "flaming"],
    "c_canopy_F": ["summary", "canopy", "flaming"],
    "c_shrub_F": ["summary", "shrub", "flaming"],
    "c_herb_F": ["summary", "nonwoody", "flaming"],
    "c_wood_F": ["summary", "woody fuels", "flaming"],
    "c_llm_F": ["summary", "litter-lichen-moss", "flaming"],
    "c_ground_F": ["summary", "ground fuels", "flaming"],
    "c_total_S": ["summary", "total", "smoldering"],
    "c_canopy_S": ["summary", "canopy", "smoldering"],
    "c_shrub_S": ["summary", "shrub", "smoldering"],
    "c_herb_S": ["summary", "nonwoody", "smoldering"],
    "c_wood_S": ["summary", "woody fuels", "smoldering"],
    "c_llm_S": ["summary", "litter-lichen-moss", "smoldering"],
    "c_ground_S": ["summary", "ground fuels", "smoldering"],
    "c_total_R": ["summary", "total", "residual"],
    "c_canopy_R": ["summary", "canopy", "residual"],
    "c_wood_R": ["summary", "woody fuels", "residual"],
    "c_llm_R": ["summary", "litter-lichen-moss", "residual"],
    "c_ground_R": ["summary", "ground fuels", "residual"],
    "c_overstory_crown": ["canopy", "overstory", "total"],
    "c_midstory_crown": ["canopy", "midstory", "total"],
    "c_understory_crown": ["canopy", "understory", "total"],
    "c_snagC1F_crown": ["canopy", "snags class 1 foliage", "total"],
    "c_snagC1F_wood": ["canopy", "snags class 1 no foliage", "total"],
    "c_snagC1_wood": ["canopy", "snags class 1 wood", "total"],
    "c_snagC2_wood": ["canopy", "snags class 2", "total"],
    "c_snagC3_wood": ["canopy", "snags class 3", "total"],
    "c_ladder": ["canopy", "ladder fuels", "total"],
    "c_shrub_1live": ["shrub", "primary dead", "total"],
    "c_shrub_1dead": ["shrub", "primary live", "total"],
    "c_shrub_2live": ["shrub", "secondary dead", "total"],
    "c_shrub_2dead": ["shrub", "secondary live", "total"],
    "c_herb_1live": ["nonwoody", "primary dead", "total"],
    "c_herb_1dead": ["nonwoody", "primary live", "total"],
    "c_herb_2live": ["nonwoody", "secondary dead", "total"],
    "c_herb_2dead": ["nonwoody", "secondary live", "total"],
    "c_wood_1hr": ["woody fuels", "1-hr fuels", "total"],
    "c_wood_10hr": ["woody fuels", "10-hr fuels", "total"],
    "c_wood_100hr": ["woody fuels", "100-hr fuels", "total"],
    "c_wood_S1000hr": ["woody fuels", "1000-hr fuels sound", "total"],
    "c_wood_R1000hr": ["woody fuels", "1000-hr fuels rotten", "total"],
    "c_wood_S10khr": ["woody fuels", "10000-hr fuels sound", "total"],
    "c_wood_R10khr": ["woody fuels", "10000-hr fuels rotten", "total"],
    "c_wood_S+10khr": ["woody fuels", "10k+-hr fuels sound", "total"],
    "c_wood_R+10khr": ["woody fuels", "10k+-hr fuels rotten", "total"],
    "c_stump_sound": ["woody fuels", "stumps sound", "total"],
    "c_stump_rotten": ["woody fuels", "stumps rotten", "total"],
    "c_stump_lightered": ["woody fuels", "stumps lightered", "total"],
    "c_litter": ["litter-lichen-moss", "litter", "total"],
    "c_lichen": ["litter-lichen-moss", "lichen", "total"],
    "c_moss": ["litter-lichen-moss", "moss", "total"],
    "c_upperduff": ["ground fuels", "duff upper", "total"],
    "c_lowerduff": ["ground fuels", "duff lower", "total"],
    "c_basal_accum": ["ground fuels", "basal accumulations", "total"],
    "c_squirrel": ["ground fuels", "squirrel middens", "total"]
}
EMISSIONS_OUTPUT_HEADER_TRANSLATIONS = {
    "e_ch4": ["total", "CH4"],
    "e_co": ["total", "CO"],
    "e_co2": ["total", "CO2"],
    "e_nmhc": ["total", "NMHC"],
    "e_pm": ["total", "PM"],
    "e_pm10": ["total", "PM10"],
    "e_pm25": ["total", "PM2.5"],
    "e_ch4_F": ["flaming", "CH4"],
    "e_co_F": ["flaming", "CO"],
    "e_co2_F": ["flaming", "CO2"],
    "e_nmhc_F": ["flaming", "NMHC"],
    "e_pm_F": ["flaming", "PM"],
    "e_pm10_F": ["flaming", "PM10"],
    "e_pm25_F": ["flaming", "PM2.5"],
    "e_ch4_S": ["smoldering", "CH4"],
    "e_co_S": ["smoldering", "CO"],
    "e_co2_S": ["smoldering", "CO2"],
    "e_nmhc_S": ["smoldering", "NMHC"],
    "e_pm_S": ["smoldering", "PM"],
    "e_pm10_S": ["smoldering", "PM10"],
    "e_pm25_S": ["smoldering", "PM2.5"],
    "e_ch4_R": ["residual", "CH4"],
    "e_co_R": ["residual", "CO"],
    "e_co2_R": ["residual", "CO2"],
    "e_nmhc_R": ["residual", "NMHC"],
    "e_pm_R": ["residual", "PM"],
    "e_pm10_R": ["residual", "PM10"],
    "e_pm25_R": ["residual", "PM2.5"]
}
EMISSIONS_DETAILS_OUTPUT_HEADER_TRANSLATIONS = {
    "ch4_canopy": ["summary", "canopy", "total", "CH4"],
    "ch4_shrub": ["summary", "shrub", "total", "CH4"],
    "ch4_herb": ["summary", "nonwoody", "total", "CH4"],
    "ch4_wood": ["summary", "woody fuels", "total", "CH4"],
    "ch4_llm": ["summary", "litter-lichen-moss", "total", "CH4"],
    "ch4_ground": ["summary", "ground fuels", "total", "CH4"],
    "co_canopy": ["summary", "canopy", "total", "CO"],
    "co_shrub": ["summary", "shrub", "total", "CO"],
    "co_herb": ["summary", "nonwoody", "total", "CO"],
    "co_wood": ["summary", "woody fuels", "total", "CO"],
    "co_llm": ["summary", "litter-lichen-moss", "total", "CO"],
    "co_ground": ["summary", "ground fuels", "total", "CO"],
    "co2_canopy": ["summary", "canopy", "total", "CO2"],
    "co2_shrub": ["summary", "shrub", "total", "CO2"],
    "co2_herb": ["summary", "nonwoody", "total", "CO2"],
    "co2_wood": ["summary", "woody fuels", "total", "CO2"],
    "co2_llm": ["summary", "litter-lichen-moss", "total", "CO2"],
    "co2_ground": ["summary", "ground fuels", "total", "CO2"],
    "nmhc_canopy": ["summary", "canopy", "total", "NMHC"],
    "nmhc_shrub": ["summary", "shrub", "total", "NMHC"],
    "nmhc_herb": ["summary", "nonwoody", "total", "NMHC"],
    "nmhc_wood": ["summary", "woody fuels", "total", "NMHC"],
    "nmhc_llm": ["summary", "litter-lichen-moss", "total", "NMHC"],
    "nmhc_ground": ["summary", "ground fuels", "total", "NMHC"],
    "pm_canopy": ["summary", "canopy", "total", "PM"],
    "pm_shrub": ["summary", "shrub", "total", "PM"],
    "pm_herb": ["summary", "nonwoody", "total", "PM"],
    "pm_wood": ["summary", "woody fuels", "total", "PM"],
    "pm_llm": ["summary", "litter-lichen-moss", "total", "PM"],
    "pm_ground": ["summary", "ground fuels", "total", "PM"],
    "pm10_canopy": ["summary", "canopy", "total", "PM10"],
    "pm10_shrub": ["summary", "shrub", "total", "PM10"],
    "pm10_herb": ["summary", "nonwoody", "total", "PM10"],
    "pm10_wood": ["summary", "woody fuels", "total", "PM10"],
    "pm10_llm": ["summary", "litter-lichen-moss", "total", "PM10"],
    "pm10_ground": ["summary", "ground fuels", "total", "PM10"],
    "pm25_canopy": ["summary", "canopy", "total", "PM2.5"],
    "pm25_shrub": ["summary", "shrub", "total", "PM2.5"],
    "pm25_herb": ["summary", "nonwoody", "total", "PM2.5"],
    "pm25_wood": ["summary", "woody fuels", "total", "PM2.5"],
    "pm25_llm": ["summary", "litter-lichen-moss", "total", "PM2.5"],
    "pm25_ground": ["summary", "ground fuels", "total", "PM2.5"]
}
HEAT_OUTPUT_HEADER_TRANSLATIONS = {
    "head_total": "total",
    "head_flaming": "flaming",
    "head_smoldering": "smoldering",
    "head_residual": "residual"
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

        fccs_id = r['fuelbeds']
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