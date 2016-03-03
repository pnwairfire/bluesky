"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import copy
import datetime
import logging

from plumerise import sev, feps, __version__ as plumerise_version

from bluesky import sun, datautils, datetimeutils

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
            #   or just let plumerise create tempdir?

            # TODO: aggregate and summarize consumption over all fuelbeds
            #   (or should this be done in consumption module?); make sure
            #   to validate that each fuelbed has consumption data
            all_consumption = datautils.summarize([fire], 'consumption')
            if not all_consumption:
                raise ValueError("Missing fire consumption data required for "
                    "FEPS plumerise")
            consumption = {
                k: v[0] for k,v in all_consumption['summary']['total'].items()
            }

            start = fire.start
            if not start:
                raise ValueError("Missing fire start time FEPS plumerise")

            # Fill in missing sunrise / sunset
            if any([fire.location.get(k) is None for k in
                    ('sunrise_hour', 'sunset_hour')]):
                # default: UTC
                utc_offset = datetimeutils.parse_utc_offset(
                    fire.location.get('utc_offset', 0.0))

                # Use NOAA-standard sunrise/sunset calculations
                tmidday = datetime.datetime(start.year, start.month, start.day, int(12))

                s = sun.Sun(lat=fire.latitude, long=fire.longitude)
                # just set them both, even if one is already set
                fire.location["sunrise_hour"] = s.sunrise_hr(tmidday) + utc_offset
                fire.location["sunset_hour"] = s.sunset_hr(tmidday) + utc_offset

            for g in fire.growth:
                if not g.get('timeprofile'):
                    raise ValueError("Missing timeprofile data required for "
                        "computing FEPS plumerise")

                g_pct = float(g['pct']) / 100.0
                g_area = fire.location['area'] * g_pct
                g_consumption = copy.deepcopy(consumption)
                datautils.multiply_nested_data(g_consumption, g_pct)

                # TODO: if managing working dir here, pass it in
                #   (I think we'll let plumerising package handle it,
                #   since we don't need to keep the output files)
                plumerise_data = pr.compute(g['timeprofile'], g_consumption,
                    fire.location)
                g['plumerise'] = plumerise_data['hours']
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
                g_frp = frp and frp * g_pct  # TODO: is this appropriate?
                plumerise_data = pr.compute(g['localmet'], g_area, frp=g_frp)
                g['plumerise'] = plumerise_data['hours']

        return _f
