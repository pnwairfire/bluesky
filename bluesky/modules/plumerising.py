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
    """
    model = fires_manager.get_config_value('plumerising', 'model',
        default='sev').lower()
    fires_manager.processed(__name__, __version__,
        plumerise_version=plumerise_version, model=model)
    if model == 'sev':
        sef_config = fires_manager.get_config_value('plumerising', 'sev',
            default={})
        pr = sev.SEVPlumeRise(**sef_config)
    else:
        raise BlueSkyConfigurationError(
            "Invalid plumerise model: '{}'".format(model))
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            if not fire.location.get('area'):
                raise ValueError(
                    "Missing fire area required for computing plumerise")
            frp = fire.get('meta', {}).get('frp')
            for g in fire.growth:
                if not g.get('localmet'):
                    raise ValueError(
                        "Missing localmet data required for computing plumerise")
                plumerise_data = pr.compute(g['localmet'], fire.location['area'],
                    frp=frp)
                g['plumerise'] = plumerise_data['hours']
    # TODO: spread out emissions over plume and set in growth or fuelbed
    #   objects ??? (be consistent with profiled emissions, setting in
    #   same place or not setting at all)

    # TODO: set summary?
    # fires_manager.summarize(plumerise=...)
