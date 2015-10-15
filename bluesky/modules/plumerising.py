"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

import plumerise

__all__ = [
    'run'
]

__version__ = "0.1.0"


def run(fires_manager, config=None):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    model = fires_manager.get_config_value('plumerise', 'model', default='sev').lower()
    fires_manager.processed(__name__, __version__,
        plumerise_version=plumerise.__version__, model=model)
    if model == 'sev':
        pr = plumerise.sev.SEVPlumeRise()
    else:
        raise BlueSkyConfigurationError(
            "Invalid plumerise model: '{}'".format(model))
    for fire in fires_manager.fires:
        if not fire.locaion.get('area'):
            raise ValueError(
                "Missing fire area required for computing plumerise")
        for g in fire.growth:
            if not g.get('localmet'):
                raise ValueError(
                    "Missing localmet data required for computing plumerise")
            g['plumerise'] = pr.compute(g['localmet'], fire.location['area'])
    # fires_manager.summarize(emissions=datautils.summarize(
    #     fires_manager.fires, 'emissions'))
