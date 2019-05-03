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
    logging.info("Running consumption module")
    # TODO: don't hard code consume_version; either update consume to define
    # it's version in consume.__version__, or execute pip:
    #   $ pip3 freeze |grep consume
    #  or
    #   $ pip3 show apps-consume4|grep "^Version:"
    fires_manager.processed(__name__, __version__,
        consume_version=CONSUME_VERSION_STR)

    # TODO: get msg_level and burn_type from fires_manager's config
    msg_level = 2  # 1 => fewest messages; 3 => most messages

    all_fuel_loadings = Config.get('consumption', 'fuel_loadings')
    fuel_loadings_manager = FuelLoadingsManager(all_fuel_loadings=all_fuel_loadings)

    _validate_input(fires_manager)

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires, or at lesat accross all fuelbeds within
    # a single fire?
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            _run_fire(fire, fuel_loadings_manager, msg_level)


    # summarise over all activity objects
    all_activity = list(itertools.chain.from_iterable(
        [f.activity for f in fires_manager.fires]))
    fires_manager.summarize(
        consumption=datautils.summarize(all_activity, 'consumption'))
    fires_manager.summarize(
        heat=datautils.summarize(all_activity, 'heat'))

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
            season = datetimeutils.season_from_date(aa.get('start'))
            for loc in aa.locations:
                for fb in loc['fuelbeds']:
                    _run_fuelbed(fb, loc, fuel_loadings_manager, season,
                        burn_type, msg_level)
                _summarize_consumption_and_heat(loc, loc['fuelbeds'])
            _summarize_consumption_and_heat(aa, aa.locations)
        _summarize_consumption_and_heat(ac, ac.get('active_areas', []))
    _summarize_consumption_and_heat(fire, fire.activity)

def _summarize_consumption_and_heat(obj, objs):
    obj['consumption'] = datautils.summarize(objs, 'consumption',
        include_details=False)
    obj['heat'] = datautils.summarize(objs, 'heat', include_details=False)


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
    # Note: consume expects area, but disregards it when computing
    #  consumption values - it produces tons per unit area (acre?), not
    #  total tons; so, to avoid confution, just set it to 1 and
    #  then correct the consumption values by multiplying by area, below
    area = (fb['pct'] / 100.0) * location['area']
    fc.fuelbed_area_acres = [1] # see see note,above
    fc.fuelbed_ecoregion = [location['ecoregion']]

    _apply_settings(fc, location, burn_type)
    _results = fc.results()
    if _results:
        # TODO: validate that _results['consumption'] and
        #   _results['heat'] are defined
        fb['consumption'] = _results['consumption']
        fb['consumption'].pop('debug', None)
        fb['heat'] = _results['heat release']

        # multiply each consumption and heat value by area if
        # output_inits is 'tons_ac',
        # TODO: multiple by area even if user sets output_units to 'tons',
        #   because consume doesn't seem to be multiplying by area for us
        #   even when 'tons' is specified
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
    'AREA_UNDEFINED': "Fire activity location data must define area for computing consumption"
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
                        # import EcoregionLookup here so that, if fires do have
                        # ecoregion defined, consumption can be run without mapscript
                        # and other dependencies installed
                        try:
                            latlng = LatLng(loc)
                            if not ecoregion_lookup:
                                from bluesky.ecoregion.lookup import EcoregionLookup
                                implemenation = Config.get('consumption',
                                    'ecoregion_lookup_implemenation')
                                ecoregion_lookup = EcoregionLookup(implemenation)
                            loc['ecoregion'] = ecoregion_lookup.lookup(
                                latlng.latitude, latlng.longitude)
                            if not loc['ecoregion']:
                                logging.warning("Failed to look up ecoregion for "
                                    "{}, {}".format(latlng.latitude, latlng.longitude))
                                _use_default_ecoregion(fires_manager, loc)

                        except exceptions.MissingDependencyError as e:
                            _use_default_ecoregion(fires_manager, loc, e)

                    for fb in loc['fuelbeds'] :
                        if not fb.get('fccs_id') or not fb.get('pct'):
                            raise ValueError("Each fuelbed must define 'fccs_id' and 'pct'")

def _use_default_ecoregion(fires_manager, loc, exc=None):
    default_ecoregion = Config.get('consumption', 'default_ecoregion')
    if default_ecoregion:
        logging.debug('Using default ecoregion %s', default_ecoregion)
        loc['location']['ecoregion'] = default_ecoregion
    else:
        logging.debug('No default ecoregion')
        if exc:
            raise exc
        else:
            raise ValueError("No default ecoregion specified.")
