"""bluesky.modules.emissions"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging

from emitcalc.calculator import EmissionsCalculator
from eflookup.fccs2ef.lookup import Fccs2Ef
from eflookup.fepsef import FepsEFLookup

__all__ = [
    'run'
]

def run(fires_manager, config=None):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    if config and config.get('emissions', 'efs').lower() == 'urbanski':
        _run_urbanski(fires_manager)
    else:
        _run_feps(fires_manager)

def _run_feps(fires_manager):
    logging.debug("Running emissions module FEPS EFs")

    # The same lookup object is used for both Rx and WF
    calculator = EmissionsCalculator(FepsEFLookup())
    for fire in fires_manager.fires:
        for fb in fire.fuelbeds:
            fb['emissions'] = calculator.calculate(fb["consumption"])

def _run_urbanski(fires_manager):
    logging.debug("Running emissions module with Urbanski EFs")

    # Instantiate two lookup object, one Rx and one WF, to be reused
    fccs2ef_wf = Fccs2Ef(is_rx=False)
    fccs2ef_rx = Fccs2Ef(is_rx=True)

    for fire in fires_manager.fires:
        fccs2ef = fccs2ef_rx if fire.get('type') == "rx" else fccs2ef_wf
        for fb in fire.fuelbeds:
            calculator = EmissionsCalculator([fccs2ef[fb["fccs_id"]]])
            fb['emissions'] = calculator.calculate(fb["consumption"])
