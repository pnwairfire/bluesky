"""bluesky.modules.emissions"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging

from emitcalc import __version__ as emitcalc_version
from emitcalc.calculator import EmissionsCalculator
from eflookup import __version__ as eflookup_version
from eflookup.fccs2ef.lookup import Fccs2Ef
from eflookup.fepsef import FepsEFLookup

import consume

from bluesky import datautils
from bluesky.exceptions import BlueSkyConfigurationError

from bluesky.consumeutils import (
    _apply_settings, FuelLoadingsManager, FuelConsumptionForEmissions, CONSUME_FIELDS
)

__all__ = [
    'run'
]
__version__ = "0.1.0"

TONS_PER_POUND = 0.0005 # 1.0 / 2000.0

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    # TODO: rename 'efs' config field as 'model', since 'consume' isn't really
    #   just a different set of EFs - uisng 'model' is more general and
    #   appropriate given the three options. (maybe still support 'efs' as an alias)
    efs = fires_manager.get_config_value('emissions', 'efs', default='feps').lower()
    species = fires_manager.get_config_value('emissions', 'species', default=[])
    include_emissions_details = fires_manager.get_config_value('emissions',
        'include_emissions_details', default=False)
    fires_manager.processed(__name__, __version__, ef_set=efs,
        emitcalc_version=emitcalc_version, eflookup_version=eflookup_version)
    if efs == 'urbanski':
        _run_urbanski(fires_manager, species, include_emissions_details)
    elif efs == 'feps':
        _run_feps(fires_manager, species, include_emissions_details)
    elif efs == 'consume':
        _run_consume(fires_manager, species, include_emissions_details)
    else:
        raise BlueSkyConfigurationError(
            "Invalid emissions factors set: '{}'".format(efs))

    summary = dict(emissions=datautils.summarize(fires_manager.fires, 'emissions'))
    if include_emissions_details:
        summary.update(emissions_details=datautils.summarize(
            fires_manager.fires, 'emissions_details'))
    fires_manager.summarize(**summary)

##
## FEPS
##

def _run_feps(fires_manager, species, include_emissions_details):
    logging.debug("Running emissions module FEPS EFs")

    # The same lookup object is used for both Rx and WF
    calculator = EmissionsCalculator(FepsEFLookup(), species=species)
    for fire in fires_manager.fires:
        if 'fuelbeds' not in fire:
            raise ValueError(
                "Missing fuelbed data required for computing emissions")
        for fb in fire.fuelbeds:
            if 'consumption' not in fb:
                raise ValueError(
                    "Missing consumption data required for computing emissions")
            _calculate(calculator, fb, include_emissions_details)
            # TODO: Figure out if we should indeed convert from lbs to tons;
            #   if so, uncomment the following
            # Note: According to BSF, FEPS emissions are in lbs/ton consumed.  Since
            # consumption is in tons, and since we want emissions in tons, we need
            # to divide each value by 2000.0
            # datautils.multiply_nested_data(fb['emissions'], TONS_PER_POUND)
            # if include_emissions_details:
            #     datautils.multiply_nested_data(fb['emissions_details'], TONS_PER_POUND)

##
## Urbanski
##

def _run_urbanski(fires_manager, species, include_emissions_details):
    logging.debug("Running emissions module with Urbanski EFs")

    # Instantiate two lookup object, one Rx and one WF, to be reused
    fccs2ef_wf = Fccs2Ef(is_rx=False)
    fccs2ef_rx = Fccs2Ef(is_rx=True)

    for fire in fires_manager.fires:
        if 'fuelbeds' not in fire:
            raise ValueError(
                "Missing fuelbed data required for computing emissions")
        fccs2ef = fccs2ef_rx if fire.get('type') == "rx" else fccs2ef_wf
        for fb in fire.fuelbeds:
            if 'consumption' not in fb:
                raise ValueError(
                    "Missing consumption data required for computing emissions")
            calculator = EmissionsCalculator([fccs2ef[fb["fccs_id"]]],
                species=species)
            _calculate(calculator, fb, include_emissions_details)
            # TODO: are these emissions factors in something other than tons
            #  per tons consumed?  if so, we need to multiply to convert
            #  values to tons

##
## CONSUME
##

def _run_consume(fires_manager, species, include_emissions_detail):
    logging.debug("Running emissions module with CONSUME")

    # look for custom fuel loadings first in the consumption config and then
    # in the emissions config
    all_fuel_loadings = fires_manager.get_config_value(
        'consumption','fuel_loadings')
    all_fuel_loadings = all_fuel_loadings or fires_manager.get_config_value(
        'emissions','fuel_loadings')
    fuel_loadings_manager = FuelLoadingsManager(
        all_fuel_loadings=all_fuel_loadings)

    for fire in fires_manager.fires:
        if 'fuelbeds' not in fire:
            raise ValueError(
                "Missing fuelbed data required for computing emissions")
        burn_type = 'activity' if fire.get('type') == "rx" else 'natural'
        for fb in fire.fuelbeds:
            if 'consumption' not in fb:
                raise ValueError(
                    "Missing consumption data required for computing emissions")
            if 'heat' not in fb:
                raise ValueError(
                    "Missing heat data required for computing emissions")

            fuel_loadings_csv_filename = fuel_loadings_manager.generate_custom_csv(
                 fb['fccs_id'])
            area = (fb['pct'] / 100.0) * fire.location['area']
            fc = FuelConsumptionForEmissions(fb["consumption"], fb['heat'],
                area, burn_type, fb['fccs_id'], fire['location'],
                fccs_file=fuel_loadings_csv_filename)

            fb['emissions_fuel_loadings'] = fuel_loadings_manager.get_fuel_loadings(fb['fccs_id'], fc.FCCS)
            e = consume.Emissions(fuel_consumption_object=fc)

            r = e.results()['emissions']
            fb['emissions'] = {f: {} for f in CONSUME_FIELDS}
            # r's key hierarchy is species > phase; we want phase > species
            for k in r:
                if k != 'stratum' and (not species or k in species):
                    for f in r[k]:
                        fb['emissions'][f][k] = r[k][f]

            # Note: We don't need to call
            #   datautils.multiply_nested_data(fb["emissions"], area)
            # because the consumption and heat data set in fc were assumed to
            # have been multiplied by area.

            # TODO: act on 'include_emissions_details'?  consume emissions
            #   doesn't provide as detailed emissions as FEPS and Urbanski;
            #   it lists per-category emissions, not per-sub-category


def _calculate(calculator, fb, include_emissions_details):
    emissions_details = calculator.calculate(fb["consumption"])
    fb['emissions'] = emissions_details['summary']['total']
    if include_emissions_details:
        fb['emissions_details'] = emissions_details
