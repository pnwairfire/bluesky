"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import consume
import logging

from plumerise import sev, feps, __version__ as plumerise_version


__all__ = [
    'run'
]

__version__ = "0.1.1"


def run(fires_manager):
    """Runs plumerise module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    compute_func = ComputeFunction(fires_manager)

    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            compute_func(fire)

    # TODO: spread out emissions over plume and set in growth or fuelbed
    #   objects ??? (be consistent with profiled emissions, setting in
    #   same place or not setting at all)

    # TODO: set summary?
    # fires_manager.summarize(plumerise=...)


class ComputeFunction(object):
    def __init__(self, fires_manager):
        model = fires_manager.get_config_value('plumerising', 'model',
            default='feps').lower()
        fires_manager.processed(__name__, __version__,
            plumerise_version=plumerise_version, model=model)

        logging.debug('Generating %s plumerise compution function', model)
        generator = getattr(self, '_{}'.format(model), None)
        if not generator:
            raise BlueSkyConfigurationError(
                "Invalid plumerise model: '{}'".format(model))

        config = fires_manager.get_config_value('plumerising', model, default={})
        self._compute_func = generator(config)

    def __call__(self, fire):
        if 'growth' not in fire:
            raise ValueError("Missing growth data required for plumerise")
        if not fire.get('location', {}).get('area'):
            raise ValueError("Missing fire area required for plumerise")
        self._compute_func(fire)

    ## compute function generators

    def _feps(self, config):
        pr = feps.FEPSPlumeRise(**config)

        def _f(fire):

            # TODO: create and change to working directory here (per fire),
            #   above (one per all fires), or below (per growth window)

            # TODO: aggregate and summarize consumption over all fuelbeds
            #   (or should this be done in consumption module?); make sure
            #   to validate that each fuelbed has consumption data
            consumption = {}

            # TODO: get this from wherever it's defined
            moisture_duff = 1

            if not consumption:
                raise ValueError("Missing fire consumption data required for "
                    "FEPS plumerise")
            for g in fire.growth:
                if not g.get('timeprofile'):
                    raise ValueError("Missing timeprofile data required for "
                        "computing FEPS plumerise")

                g_pct = float(g['pct']) / 100.0
                g_area = fire.location['area'] * g_pct
                g_consumption = copy.deepcopy(consumption)
                g_moisture_duff = moisture_duff * g_pct
                datautils.multiply_nested_data(g_consumption, g_pct)
                multiply_nested_data(g['plumerise'])

                plumerise_data = pr.compute(g['time_profile'], g_consumption, g_moisture_duff, g_area)
                g['plumerise'] = plumerise_data['plumerise']
                # TODO: do anything with plumerise_data['heat'] ?

        return _f

    def _sev(self, config):
        pr = sev.SEVPlumeRise(**config)

        def _f(fire):
            frp = fire.get('meta', {}).get('frp')
            for g in fire.growth:
                if not g.get('localmet'):
                    raise ValueError(
                        "Missing localmet data required for computing SEV plumerise")
                g_pct = float(g['pct']) / 100.0
                g_area = fire.location['area'] * g_pct
                g_frp = frp * g_pct  # TODO: is this appropriate?
                plumerise_data = pr.compute(g['localmet'], g_area, frp=g_frp)
                g['plumerise'] = plumerise_data['hours']

        return _f
