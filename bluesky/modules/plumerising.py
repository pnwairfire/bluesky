"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

from plumerise import sev, __version__ as plumerise_version


__all__ = [
    'run'
]

__version__ = "0.1.0"


def run(fires_manager):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    Kwargs:
     - config -- optional configparser object
    """
    model = fires_manager.get_config_value('plumerise', 'model',
        default='sev').lower()
    fires_manager.processed(__name__, __version__,
        plumerise_version=plumerise_version, model=model)
    if model == 'sev':
        sef_config = fires_manager.get_config_value('plumerise', 'sev',
            default={})
        pr = sev.SEVPlumeRise(**sef_config)
    else:
        raise BlueSkyConfigurationError(
            "Invalid plumerise model: '{}'".format(model))
    for fire in fires_manager.fires:
        if not fire.location.get('area'):
            raise ValueError(
                "Missing fire area required for computing plumerise")
        for g in fire.growth:
            if not g.get('localmet'):
                raise ValueError(
                    "Missing localmet data required for computing plumerise")
            g['plumerise'] = pr.compute(g['localmet'], fire.location['area'])
    # fires_manager.summarize(emissions=datautils.summarize(
    #     fires_manager.fires, 'emissions'))
