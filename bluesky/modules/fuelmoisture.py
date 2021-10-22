"""bluesky.modules.fuelmoisture"""

__author__ = "Joel Dubowy"

import logging


from afdatetime.parsing import parse as parse_dt

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.fuelmoisture import wims, nfdrs, fill_in_defaults
from bluesky.locationutils import LatLng


__all__ = [
    'run'
]

__version__ = "0.1.0"

MODELS = {
    'wims': wims.WimsFuelMoisture,
    'nfdrs': nfdrs.NfdrsFuelMoisture
}
VALID_MODELS = set(MODELS.keys())

def run(fires_manager):
    """Runs emissions module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    models = [m.lower() for m in Config().get('fuelmoisture', 'models')]
    fires_manager.processed(__name__, __version__, models=models,
        wims_version=wims.__version__, nfdrs_version=nfdrs.__version__)

    if not VALID_MODELS.issuperset(models):
        raise BlueSkyConfigurationError(
            "Invalid fuel moisture model(s): {}".format(
                set(models).difference(VALID_MODELS)))

    logging.debug('Using fuel moisture model(s) %s', ','.join(models))
    fms = [MODELS[m]() for m in models]

    use_defaults = Config().get('fuelmoisture', 'use_defaults')
    logging.debug('Use default values for any undefined fuel '
        'moisture fields: %s', fill_in_defaults)

    skip_failures = Config().get('fuelmoisture', 'skip_failures')

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            for aa in fire.active_areas:
                start = parse_dt(aa['start']).date()

                # Note that aa.locations validates that each location object
                # has either lat+lng+area or polygon
                for loc in aa.locations:
                    loc['fuelmoisture'] = {}
                    for fm in fms:
                        try:
                            fm.set_fuel_moisture(aa, loc)
                        except Exception as e:
                            latlng = LatLng(loc)
                            logging.error("Failed to compute fuel moisture for "
                                f"loc {latlng.latitude}, {latlng.longitude} "
                                f"using model {fm}: {e}")
                            if skip_failures:
                                continue
                            raise

                    if use_defaults:
                        fill_in_defaults(fire, aa, loc)
