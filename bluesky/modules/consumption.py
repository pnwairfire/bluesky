"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import itertools
import logging

import consume

from bluesky import datautils
from bluesky.consumeutils import _apply_settings, FuelLoadingsManager
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
    #   $ pip freeze |grep consume
    #  or
    #   $ pip show apps-consume4|grep "^Version:"
    fires_manager.processed(__name__, __version__,
        consume_version="4.1.2")

    # TODO: get msg_level and burn_type from fires_manager's config
    msg_level = 2  # 1 => fewest messages; 3 => most messages

    all_fuel_loadings = fires_manager.get_config_value('consumption',
        'fuel_loadings')
    fuel_loadings_manager = FuelLoadingsManager(all_fuel_loadings=all_fuel_loadings)

    _validate_input(fires_manager)

    # TODO: can I safely instantiate one FuelConsumption object and
    # use it across all fires, or at lesat accross all fuelbeds within
    # a single fire?
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            _run_fire(fire, fuel_loadings_manager, msg_level)


    # summarise over all growth objects
    all_growth = list(itertools.chain.from_iterable(
        [f.growth for f in fires_manager.fires]))
    fires_manager.summarize(
        consumption=datautils.summarize(all_growth, 'consumption'))
    fires_manager.summarize(
        heat=datautils.summarize(all_growth, 'heat'))

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
    for g in fire.growth:
        for fb in g['fuelbeds']:
            _run_fuelbed(fb, fuel_loadings_manager, g['location'], burn_type, msg_level)
        # Aggregate consumption and heat over all fuelbeds in the growth window
        # include only per-phase totals, not per category > sub-category > phase
        g['consumption'] = datautils.summarize([g], 'consumption',
            include_details=False)
        g['heat'] = datautils.summarize([g], 'heat', include_details=False)

    # Aggregate consumption and heat over all fuelbeds in *all* growth windows;
    # include only per-phase totals, not per category > sub-category > phase
    fire.consumption = datautils.summarize(fire.growth, 'consumption',
        include_details=False)
    fire.heat = datautils.summarize(fire.growth, 'heat',
        include_details=False)

def _run_fuelbed(fb, fuel_loadings_manager, location, burn_type, msg_level):
    fuel_loadings_csv_filename = fuel_loadings_manager.generate_custom_csv(
        fb['fccs_id'])

    fc = consume.FuelConsumption(
        fccs_file=fuel_loadings_csv_filename) #msg_level=msg_level)

    fb['fuel_loadings'] = fuel_loadings_manager.get_fuel_loadings(fb['fccs_id'], fc.FCCS)

    fc.burn_type = burn_type
    fc.fuelbed_fccs_ids = [fb['fccs_id']]

    # Note: if we end up running fc on all fuelbeds at once, use lists
    # for the rest
    # Note: consume expects area, but disregards it when computing
    #  consumption values - it produces tons per unit area (acre?), not
    #  total tons; the consumption values will be multiplied by area, below
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



def _validate_input(fires_manager):
    ecoregion_lookup = None # instantiate only if necessary
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            if not fire.get('growth'):
                raise ValueError(
                    "Missing growth data required for computing consumption")
            for g in fire.growth:
                for k in ('fuelbeds', 'location'):
                    if not g.get(k):
                        raise ValueError("Missing growth '{}' data required "
                        "for computing consumption".format(k))
                # only 'area' is required from location
                if not g['location'].get('area'):
                    raise ValueError("Fire growth location data must "
                        "define area for computing consumption")
                if not g['location'].get('ecoregion'):
                    # import EcoregionLookup here so that, if fires do have
                    # ecoregion defined, consumption can be run without mapscript
                    # and other dependencies installed
                    try:
                        latlng = LatLng(g['location'])
                        if not ecoregion_lookup:
                            from bluesky.ecoregion.lookup import EcoregionLookup
                            implemenation = fires_manager.get_config_value(
                                'consumption', 'ecoregion_lookup_implemenation',
                                default='ogr')
                            ecoregion_lookup = EcoregionLookup(implemenation)
                        g['location']['ecoregion'] = ecoregion_lookup.lookup(
                            latlng.latitude, latlng.longitude)
                    except exceptions.MissingDependencyError:
                        default_ecoregion = fires_manager.get_config_value(
                            'consumption', 'default_ecoregion')
                        if default_ecoregion:
                            g['location']['ecoregion'] = default_ecoregion
                        else:
                            raise

                for fb in g['fuelbeds'] :
                    if not fb.get('fccs_id') or not fb.get('pct'):
                        raise ValueError("Each fuelbed must define 'fccs_id' and 'pct'")
