"""bluesky.modules.fuelmoisture"""

__author__ = "Joel Dubowy"

import logging


from afdatetime.parsing import parse_dt

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.fuelmoisture import wims


__all__ = [
    'run'
]

__version__ = "0.1.0"

MODELS = {
    'wims': WimsFuelMoisture
}

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    model = Config('fuelmoisture', 'model').lower()
    fires_manager.processed(__name__, __version__, model=model,
        wims_version=wims.__version__)

    if model not in MODELS:
        raise BlueSkyConfigurationError(
            "Invalid fuel moisture module: {}".format(model))

    logging.debug('Using fuel moisture model %s', model)
    fm = MODELS[model]()

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for aa in fire.active_areas:
                start = parse_dt(aa['start']).date()

                # Note that aa.locations validates that each location object
                # has either lat+lng+area or polygon
                for loc in aa.locations:
                    fm.set_fuel_moisture(aa, loc)
