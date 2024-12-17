"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import itertools
import io
import json
import logging
import re
import subprocess
from contextlib import redirect_stdout

import consume

from bluesky.config import Config
from bluesky import datautils, datetimeutils
from bluesky.consumeutils import (
    _apply_settings, FuelLoadingsManager, CONSUME_VERSION_STR
)
from bluesky import exceptions
from bluesky.locationutils import LatLng


__all__ = [
    'run'
]

__version__ = "0.1.0"


SUMMARIZE_FUEL_LOADINGS = Config().get('consumption', 'summarize_fuel_loadings')
LOADINGS_KEY_MATCHER = re.compile('.*_loading')

def run(fires_manager):
    """Runs the fire data through consumption calculations, using the consume
    package for the underlying computations.

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    # TODO: don't hard code consume_version; either update consume to define
    # it's version in consume.__version__, or execute pip:
    #   $ pip3 freeze |grep consume
    #  or
    #   $ pip3 show apps-consume4|grep "^Version:"
    fires_manager.processed(__name__, __version__,
        consume_version=CONSUME_VERSION_STR)

    all_fuel_loadings = Config().get('consumption', 'fuel_loadings')
    fuel_loadings_manager = FuelLoadingsManager(all_fuel_loadings=all_fuel_loadings)

    _validate_input(fires_manager)

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires, or at lesat accross all fuelbeds within
    # a single fire?
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            _run_fire(fire, fuel_loadings_manager)

    datautils.summarize_all_levels(fires_manager, 'consumption')
    datautils.summarize_all_levels(fires_manager, 'heat')
    if SUMMARIZE_FUEL_LOADINGS:
        datautils.summarize_all_levels(fires_manager, 'fuel_loadings',
            data_key_matcher=LOADINGS_KEY_MATCHER)

def _run_fire(fire, fuel_loadings_manager):
    logging.debug("Consume consumption - fire {}".format(fire.id))

    # TODO: set burn type to 'activity' if fire.fuel_type == 'piles' ?
    if fire.fuel_type == 'piles':
        raise ValueError("Consume can't be used for fuel type 'piles'")
    burn_type = fire.fuel_type
    fire_type = fire.type

    # TODO: can I run consume on all fuelbeds at once and get per-fuelbed
    # results?  If it is simply a matter of parsing separated values from
    # the results, make sure that running all at once produces any performance
    # gain; if it doesn't,then it might not be worth the trouble
    for ac in fire['activity']:
        for aa in ac.active_areas:
            if not aa.get('start'):
                raise RuntimeError(
                    "Active area start time required to run consumption.")

            season = datetimeutils.season_from_date(aa.get('start'))
            for loc in aa.locations:
                # If this location has piles, we'll get a piles specific fuel
                # loadings manager to pass into consume. These fuel loadings will
                # be the same for each fuelbed, so create them once and then
                # create a
                loc_fuel_loadings_manager = (
                    get_piles_fuel_loadings_manager(loc) or fuel_loadings_manager
                )

                for fb in loc['fuelbeds']:
                    fb_area = loc['area'] * (fb['pct'] / 100)
                    fb_fuel_loadings_manager = FuelLoadingsManager(all_fuel_loadings={
                        fb['fccs_id']: { k: v / fb_area for k, v in fb['fuel_loadings'].items() }
                    }) if fb.get('fuel_loadings') else loc_fuel_loadings_manager

                    _run_fuelbed(fb, loc, fb_fuel_loadings_manager, season,
                        burn_type, fire_type)

                # scale with estimated consumption or fuel load, if specified
                # and if configured to do so
                (_scale_with_estimated_consumption(loc)
                    or _scale_with_estimated_fuelload(loc))


SCALE_WITH_ESTIMATED_CONSUMPTION = Config().get('consumption',
    'scale_with_estimated_consumption')

def _scale_with_estimated_consumption(loc):
    if (not SCALE_WITH_ESTIMATED_CONSUMPTION
            or not loc.get('input_est_consumption_tpa')):
        return False

    # get total modeled consumption per acre; note that values in
    # 'consumption' are total (not per acre)
    modeled_consumption_tpa = 0
    for fb in loc['fuelbeds']:
        modeled_consumption_tpa += fb['consumption']['summary']['total']['total'][0]
    modeled_consumption_tpa /= loc['area']

    scale_factor = loc['input_est_consumption_tpa'] / modeled_consumption_tpa
    logging.debug("Using consumption scale factor %s", scale_factor)

    for fb in loc['fuelbeds']:
        datautils.multiply_nested_data(fb["consumption"], scale_factor)

    loc['input_est_consumption_scale_factor'] = scale_factor

    return True

SCALE_WITH_ESTIMATED_FUELLOAD = Config().get('consumption',
    'scale_with_estimated_fuelload')

def _scale_with_estimated_fuelload(loc):
    if (not SCALE_WITH_ESTIMATED_FUELLOAD
            or not loc.get('input_est_fuelload_tpa')
            or any([not fb.get('fuel_loadings') for fb in loc['fuelbeds']])):
        return False

    # get total modeled fuel load per acre; note
    # that values in 'fuel_loadings' are total, not per acre
    # We'll all sum fuel loadings values except for 'total_'
    # (which is only 'total_available_fuel_loading')
    loadings_keys_to_sum = [
        k for k in loc['fuelbeds'][0]['fuel_loadings']
            if k.endswith('_loading') and not k.startswith('total_')
    ]
    modeled_fuelload_tpa = 0
    for fb in loc['fuelbeds']:
        modeled_fuelload_tpa += sum([fb['fuel_loadings'][k] for k in loadings_keys_to_sum])
    modeled_fuelload_tpa /= loc['area']
    logging.debug("Modeled fuel loading (per acre) %s", modeled_fuelload_tpa)

    scale_factor = loc['input_est_fuelload_tpa'] / modeled_fuelload_tpa
    logging.debug("Using fuel loadings scale factor %s", scale_factor)

    loadings_keys_to_scale = [
        k for k in loc['fuelbeds'][0]['fuel_loadings'] if k.endswith('_loading')
    ]
    for fb in loc['fuelbeds']:
        # adjust fuel load values
        for k in loadings_keys_to_scale:
            fb['fuel_loadings'][k] *= scale_factor

        # adjust consumption values
        datautils.multiply_nested_data(fb["consumption"], scale_factor)

        # adjust heat values
        datautils.multiply_nested_data(fb["heat"], scale_factor)

    loc['input_est_fuelload_scale_factor'] = scale_factor

    return True

def get_piles_fuel_loadings_manager(loc):
    """If piles related fields are defined for this location, this method
    returns fuel loadings specific for the described piles.

    For piles, we call the pile calculator to get pile mass and mass consumed.
    We compute mass per acre and pass it into consume via custom fuel loadings.
    We use the total mass consumed and pile mass values to compute
    `pile_blackened_pct`, which is also passed into CONSUME.  The reason for
    using CONSUME, rather than just directly using the consumption value
    returned by the piles calculator, is to get phase specific values.

    Note that, if loc['piles'] is defined, the location is assumed to have
    *only* piles.  If the actual physical location has both piles and natural
    fuels, they need to be specified as two different locations (specified
    points or perimeters) in the bluesky input data.
    """
    if not loc.get('piles'):
        # No piles at this location
        return None

    try:
        totals = { 'mass': 0, 'consumed': 0 } # to compute overall pct consumed
        mass_per_acre = {k: 0 for k in FuelLoadingsManager.FUEL_LOADINGS_KEY_MAPPINGS.values()}

        # support either array of piles or single piles dict
        piles = loc['piles'] if hasattr(loc['piles'], 'append') else [loc['piles']]

        for p in piles:
            if p.get('unit_system') and p['unit_system'] != 'English':
                raise ValueError('Only English unit supported for piles')
            p['unit_system'] = 'English'

            pile_type = p.pop('pile_type', None)
            if pile_type not in ('Hand', 'Machine'):
                raise ValueError("Pile type ('Hand' or 'Machine') must be specified")

            args = ['piles-calc', pile_type] + list(itertools.chain.from_iterable(
                [['--'+ k.replace('_','-'), str(p[k])] for k in p]))
            output_json = subprocess.check_output(args,
                stderr=subprocess.STDOUT, universal_newlines=True)
            output = json.loads(output_json)

            # The piles loadings keys are 'pile_clean_loading',
            #  'pile_dirty_loading', and 'pile_vdirty_loading'
            quality = p.get('pile_quality', 'Clean').lower().replace('verydirty', 'vdirty')
            key = f"pile_{quality}_loading"
            mass_per_acre[key] += output['pileMass'] / loc['area']
            totals['mass'] += output['pileMass']
            totals['consumed'] += output['consumedMass']

        # the piles calculator already takes into account percent consumed,
        # so we can just set pile_blackened_pct to 100
        # TODO: should we instead set `percentConsumed` to 100 in the call
        #   to `piles-calc` and then set `pile_blackened_pct` to `percentConsumed` ?
        loc['pile_blackened_pct'] = 100 * (totals['consumed'] / totals['mass'])

        return FuelLoadingsManager(all_fuel_loadings={
            fb['fccs_id']: mass_per_acre for fb in loc['fuelbeds']
        })

    except Exception as e:
        logging.error(f'Failed to calculate pile mass: {e}')
        if not Config().get('consumption', 'piles', 'use_default_loadings_on_failure'):
            raise e
        # else, returns none; non-piles fuel loadins will be used

def _run_fuelbed(fb, location, fuel_loadings_manager, season,
        burn_type, fire_type):
    fuel_loadings_csv_filename = fuel_loadings_manager.generate_custom_csv(
        fb['fccs_id'])

    fc = consume.FuelConsumption(
        fccs_file=fuel_loadings_csv_filename,
        msg_level=logging.root.level)

    fb['fuel_loadings'] = fuel_loadings_manager.get_fuel_loadings(fb['fccs_id'], fc.FCCS)

    fc.burn_type = burn_type
    fc.fuelbed_fccs_ids = [fb['fccs_id']]
    fc.season = [season]

    # Note: if we end up running fc on all fuelbeds at once, use lists
    # for the rest
    # Note: consumption output is always returned in tons per acre
    #  (see comment, below) and is linearly related to area, so the
    #  consumption values are the same regardless of what we set
    #  fuelbed_area_acres to.  Released heat output, on the other hand,
    #  is not linearly related to area, so we need to set area
    area = (fb['pct'] / 100.0) * location['area']
    fc.fuelbed_area_acres = [area]
    fc.fuelbed_ecoregion = [location['ecoregion']]

    # In an error situation these two calls print errors to stdout
    # which we have to capture to include in our error message.
    stdout_target = io.StringIO()
    with redirect_stdout(stdout_target):
        _apply_settings(fc, location, burn_type, fire_type)
        _results = fc.results()

    if _results:
        # TODO: validate that _results['consumption'] and
        #   _results['heat'] are defined
        fb['consumption'] = _results['consumption']
        fb['consumption'].pop('debug', None)
        fb['heat'] = _results['heat release']

        # Multiply each consumption value by area if output_inits is 'tons_ac'
        # Note: regardless of what fc.output_units is set to, it gets
        #  reset to 'tons_ac' in the call to fc.results, and the output values
        #  are the same (presumably always in tons_ac)
        # Also multiply heat by area, though we're currently not sure if the
        # units are in fact BTU per acre
        if fc.output_units == 'tons_ac':
            datautils.multiply_nested_data(fb["consumption"], area)
            datautils.multiply_nested_data(fb["heat"], area)
            datautils.multiply_nested_data(fb["fuel_loadings"], area,
                data_key_matcher=LOADINGS_KEY_MATCHER)

    else:
        raise RuntimeError("Failed to calculate consumption for "
            "fuelbed {}: {}".format(fb['fccs_id'], stdout_target.getvalue()))

VALIDATION_ERROR_MSGS = {
    'NO_ACTIVITY': "Fire missing activity data required for computing consumption",
    'NO_LOCATIONS': "Active area missing location data required for computing consumption",
    'NO_FUELBEDS': "Active area location missing fuelbeds data required for computing consumption",
    'AREA_UNDEFINED': "Fire activity location data must define area for computing consumption",
    'ECOREGION_REQUIED': 'Fire activity location data must define ecoregion for computing consumption. Run the ecoregion module first.',
    'FCCS_ID_AND_PCT_REQUIRED': "Each fuelbed must define 'fccs_id' and 'pct'"
}

def _validate_input(fires_manager):
    ecoregion_lookup = None # instantiate only if necessary
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            active_areas = fire.active_areas
            if not active_areas:
                raise ValueError(VALIDATION_ERROR_MSGS['NO_ACTIVITY'])

            for aa in active_areas:
                locations = aa.locations
                if not locations:
                    raise ValueError(VALIDATION_ERROR_MSGS["NO_LOCATIONS"])

                for loc in locations:
                    if not loc.get('fuelbeds'):
                        raise ValueError(VALIDATION_ERROR_MSGS["NO_FUELBEDS"])

                    # only 'area' is required from location
                    if not loc.get('area'):
                        raise ValueError(VALIDATION_ERROR_MSGS["AREA_UNDEFINED"])

                    if not loc.get('ecoregion'):
                        raise ValueError(VALIDATION_ERROR_MSGS["ECOREGION_REQUIED"])

                    for fb in loc['fuelbeds'] :
                        # make sure that FCCS id is defined and that pct is defined and non-zero
                        # Note: FCCS id is expected to be a string, but integer values are
                        #    accepted, so check `fb.get('fccs_id') in (None, "")` instead of
                        #    `not fb.get('fccs_id')` to allow for integer zero value for
                        #    FCCS #0 (bare ground / light fuels)
                        if fb.get('fccs_id') in (None, "") or not fb.get('pct'):
                            raise ValueError(VALIDATION_ERROR_MSGS['FCCS_ID_AND_PCT_REQUIRED'])
