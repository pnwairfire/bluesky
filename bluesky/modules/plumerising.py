"""bluesky.modules.plumerise

Requires time profiled emissions and localmet data.
"""

__author__ = "Joel Dubowy"

import copy
import datetime
import logging
import os

from plumerise import sev, feps, __version__ as plumerise_version
from pyairfire import sun

from bluesky import datautils, datetimeutils, locationutils

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

        if 'working_dir' in config:
            fires_manager.plumerising = {
                'output': {
                    'directory': config['working_dir']
                }
            }

    def __call__(self, fire):
        if 'growth' not in fire:
            raise ValueError("Missing growth data required for plumerise")
        if any([not g.get('location', {}).get('area') for g in fire.growth]):
            raise ValueError("Missing fire growth area required for plumerise")
        self._compute_func(fire)

    ## compute function generators

    def _feps(self, config):
        pr = feps.FEPSPlumeRise(**config)

        def _get_working_dir(fire):
            if 'working_dir' in config:
                working_dir = os.path.join(config['working_dir'],
                    "feps-plumerise-{}".format(fire.id))
                if not os.path.exists(working_dir):
                    os.makedirs(working_dir)
                return working_dir

        def _f(fire):
            # TODO: create and change to working directory here (per fire),
            #   above (one working dir per all fires), or below (per growth
            #   window)...or just let plumerise create temp workingdir (as
            #   it's currently doing?
            for g in fire.growth:
                if not g.get('consumption', {}).get('summary'):
                    raise ValueError("Missing fire growth consumption data "
                        "required for FEPS plumerise")

                # Fill in missing sunrise / sunset
                if any([g['location'].get(k) is None for k in
                        ('sunrise_hour', 'sunset_hour')]):
                    start = datetimeutils.parse_datetime(g['start'], 'start')
                    if not start:
                        raise ValueError("Missing fire growth start time "
                            "required by FEPS plumerise")

                    # default: UTC
                    utc_offset = datetimeutils.parse_utc_offset(
                        g['location'].get('utc_offset', 0.0))

                    # Use NOAA-standard sunrise/sunset calculations
                    latlng = locationutils.LatLng(g['location'])
                    s = sun.Sun(lat=latlng.latitude, lng=latlng.longitude)
                    d = start.date()
                    # just set them both, even if one is already set
                    g['location']["sunrise_hour"] = s.sunrise_hr(d, utc_offset)
                    g['location']["sunset_hour"] = s.sunset_hr(d, utc_offset)

                if not g.get('timeprofile'):
                    raise ValueError("Missing timeprofile data required for "
                        "computing FEPS plumerise")

                plumerise_data = pr.compute(g['timeprofile'],
                    g['consumption']['summary'], g['location'],
                    working_dir=_get_working_dir(fire))
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
                # TODO: if frp is defined, do we need to multiple by growth's
                #   percentage of the fire's total area?
                g_frp = frp
                plumerise_data = pr.compute(g['localmet'],
                    g['location']['area'], frp=g_frp)
                g['plumerise'] = plumerise_data['hours']

        return _f
