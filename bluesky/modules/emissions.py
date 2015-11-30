"""bluesky.modules.emissions"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging

from emitcalc import __version__ as emitcalc_version
from emitcalc.calculator import EmissionsCalculator
from eflookup import __version__ as eflookup_version
from eflookup.fccs2ef.lookup import Fccs2Ef
from eflookup.fepsef import FepsEFLookup

from bluesky import datautils
from bluesky.exceptions import BlueSkyConfigurationError

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
    else:
        raise BlueSkyConfigurationError(
            "Invalid emissions factors set: '{}'".format(efs))

    summary = dict(emissions=datautils.summarize(fires_manager.fires, 'emissions'))
    if include_emissions_details:
        summary.update(emissions_details=datautils.summarize(
            fires_manager.fires, 'emissions_details'))
    fires_manager.summarize(**summary)

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

def _calculate(calculator, fb, include_emissions_details):
    emissions_details = calculator.calculate(fb["consumption"])
    fb['emissions'] = emissions_details['summary']['total']
    if include_emissions_details:
        fb['emissions_details'] = emissions_details
