"""bluesky.modules.emissions"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging

import emitcalc
from emitcalc.calculator import EmissionsCalculator
from eflookup.fccs2ef.lookup import Fccs2Ef
from eflookup.fepsef import FepsEFLookup

from bluesky import datautils
from bluesky.configuration import get_config_value
from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'run'
]
__version__ = "0.1.0"

def run(fires_manager, config=None):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    efs = get_config_value(config, 'emissions', 'efs', 'feps').lower()
    fires_manager.processed(__name__, __version__,
        emitcalc_version=emitcalc.__version__, ef_set=efs)
    if efs == 'urbanski':
        _run_urbanski(fires_manager)
    elif efs == 'feps':
        _run_feps(fires_manager)
    else:
        raise BlueSkyConfigurationError(
            "Invalid emissions factors set: '{}'".format(efs))
    fires_manager.summarize(emissions=datautils.summarize(fires_manager.fires))

def _run_feps(fires_manager):
    logging.debug("Running emissions module FEPS EFs")

    # The same lookup object is used for both Rx and WF
    calculator = EmissionsCalculator(FepsEFLookup())
    for fire in fires_manager.fires:
        if 'fuelbeds' not in fire:
            raise ValueError("Missing fuelbed data required for computing emissions")
        for fb in fire.fuelbeds:
            if 'consumption' not in fb:
                raise ValueError("Missing consumption data required for computing emissions")
            fb['emissions'] = calculator.calculate(fb["consumption"])

def _run_urbanski(fires_manager):
    logging.debug("Running emissions module with Urbanski EFs")

    # Instantiate two lookup object, one Rx and one WF, to be reused
    fccs2ef_wf = Fccs2Ef(is_rx=False)
    fccs2ef_rx = Fccs2Ef(is_rx=True)

    for fire in fires_manager.fires:
        if 'fuelbeds' not in fire:
            raise ValueError("Missing fuelbed data required for computing emissions")
        fccs2ef = fccs2ef_rx if fire.get('type') == "rx" else fccs2ef_wf
        for fb in fire.fuelbeds:
            if 'consumption' not in fb:
                raise ValueError("Missing consumption data required for computing emissions")
            calculator = EmissionsCalculator([fccs2ef[fb["fccs_id"]]])
            fb['emissions'] = calculator.calculate(fb["consumption"])
