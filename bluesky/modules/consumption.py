"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import itertools
import logging
import re

import consume

from bluesky.config import Config
from bluesky import datautils, datetimeutils
from bluesky.consumption.consume.consumeutils import (
    _get_setting, _apply_settings, FuelLoadingsManager, CONSUME_VERSION_STR
)
from bluesky.consumption.consume.precomputed import look_up
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
                for fb in loc['fuelbeds']:
                    if Config().get('consumption', 'precomputed', 'enabled'):
                        try:
                            _lookup_precomputed(fb, loc, fuel_loadings_manager,
                                season, burn_type, fire_type)

                        except Exception as e:
                            logging.warning("Failed to look up precomputed consume data."
                                " Running conume in realtime. Error: %s", e)
                            if Config().get('consumption', 'precomputed', 'run_consume_on_failure'):
                                fb.pop("consumption", None)
                                fb.pop("heat", None)
                                _run_fuelbed(fb, loc, fuel_loadings_manager, season,
                                    burn_type, fire_type)
                            else:
                                raise

                    else:
                        _run_fuelbed(fb, loc, fuel_loadings_manager, season,
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

    # get fuel loadings keys from first fuelbed
    loadings_keys = [k for k in loc['fuelbeds'][0]['fuel_loadings'] if k.endswith('_loading')]

    # get total modeled fuel load per acre; note that values in 'fuel_loadings' are per acre
    modeled_fuelload_tpa = 0
    for fb in loc['fuelbeds']:
        modeled_fuelload_tpa += sum([fb['fuel_loadings'][k] for k in loadings_keys])
    logging.debug("Modeled fuel loading (per acre) %s", modeled_fuelload_tpa)

    scale_factor = loc['input_est_fuelload_tpa'] / modeled_fuelload_tpa
    logging.debug("Using fuel loadings scale factor %s", scale_factor)

    for fb in loc['fuelbeds']:
        # adjust fuel load values
        for k in loadings_keys:
            fb['fuel_loadings'][k] *= scale_factor

        # adjust consumption values
        datautils.multiply_nested_data(fb["consumption"], scale_factor)

    loc['input_est_fuelload_scale_factor'] = scale_factor

    return True

def _lookup_precomputed(fb, location, fuel_loadings_manager, season,
        burn_type, fire_type):
    thousand_hr_fm = _get_setting(location,'fuel_moisture_1000hr_pct')
    duff_fm = _get_setting(location, 'fuel_moisture_duff_pct')
    litter_fm = _get_setting(location, 'fuel_moisture_litter_pct')

    c, h = look_up(fb['fccs_id'], fire_type, burn_type, season,
        thousand_hr_fm, duff_fm, litter_fm)

    fb["consumption"] = c
    fb["heat"] = h

    area = (fb['pct'] / 100.0) * location['area']
    datautils.multiply_nested_data(fb["consumption"], area)
    datautils.multiply_nested_data(fb["heat"], area)

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

    # TODO: see comment, below, re. capturing err messages when applying settings
    _apply_settings(fc, location, burn_type, fire_type)

    # TODO: see comment, below, re. capturing err messages when computing results
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
        # TODO: somehow get error information from fc object; when
        #   you call fc.results() in an error situation, it writes to
        #   stdout or stderr (?), something like:
        #
        #     !!! Error settings problem, the following are required:
        #            fm_type
        #
        #   And sometimes you see error output to stdout or stderr (?)
        #   when `_apply_settings` is called, above.  e.g.:
        #
        #     Error: the following values are not permitted for setting fm_duff:
        #     [203]
        #
        #     Error settings problem ---> {'fm_duff'}
        #
        #   it would be nice to access that error message here and
        #   include it in the exception message
        raise RuntimeError("Failed to calculate consumption for "
            "fuelbed {}".format(fb['fccs_id']))

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
