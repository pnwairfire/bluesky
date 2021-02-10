"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import itertools
import logging

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

    # TODO: get msg_level and burn_type from fires_manager's config
    msg_level = 2  # 1 => fewest messages; 3 => most messages

    all_fuel_loadings = Config().get('consumption', 'fuel_loadings')
    fuel_loadings_manager = FuelLoadingsManager(all_fuel_loadings=all_fuel_loadings)

    _validate_input(fires_manager)

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires, or at lesat accross all fuelbeds within
    # a single fire?
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            _run_fire(fire, fuel_loadings_manager, msg_level)

    datautils.summarize_all_levels(fires_manager, 'consumption')
    datautils.summarize_all_levels(fires_manager, 'heat')

def _run_fire(fire, fuel_loadings_manager, msg_level):
    logging.debug("Consume consumption - fire {}".format(fire.id))

    # TODO: set burn type to 'activity' if fire.fuel_type == 'piles' ?
    if fire.fuel_type == 'piles':
        raise ValueError("Consume can't be used for fuel type 'piles'")
    burn_type = fire.fuel_type

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
                    _run_fuelbed(fb, loc, fuel_loadings_manager, season,
                        burn_type, msg_level)

def _run_fuelbed(fb, location, fuel_loadings_manager, season,
        burn_type, msg_level):
    fuel_loadings_csv_filename = fuel_loadings_manager.generate_custom_csv(
        fb['fccs_id'])

    fc = consume.FuelConsumption(
        fccs_file=fuel_loadings_csv_filename) #msg_level=msg_level)

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

    _apply_settings(fc, location, burn_type)
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

    else:
        # TODO: somehow get error information from fc object; when
        #   you call fc.results() in an error situation, it writes to
        #   stdout or stderr (?), something like:
        #
        #     !!! Error settings problem, the following are required:
        #            fm_type
        #   it would be nice to access that error message here and
        #   include it in the exception message
        raise RuntimeError("Failed to calculate consumption for "
            "fuelbed {}".format(fb['fccs_id']))

VALIDATION_ERROR_MSGS = {
    'NO_ACTIVITY': "Fire missing activity data required for computing consumption",
    'NO_LOCATIONS': "Active area missing location data required for computing consumption",
    'NO_FUELBEDS': "Active area location missing fuelbeds data required for computing consumption",
    'AREA_UNDEFINED': "Fire activity location data must define area for computing consumption",
    'ECOREGION_REQUIED': 'Fire activity location data must define ecoregion for computing consumption'
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
                        if not fb.get('fccs_id') or not fb.get('pct'):
                            raise ValueError("Each fuelbed must define 'fccs_id' and 'pct'")
