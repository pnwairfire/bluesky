"""bluesky.modules.timeprofile"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import timeprofile
from timeprofile.static import (
    StaticTimeProfiler,
    InvalidDailyHourlyFractionsError,
    InvalidStartEndTimesError,
    InvalidEmissionsDataError
)

from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'run'
]
__version__ = "0.1.0"

def run(fires_manager):
    """Runs timeprofile module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    daily_hourly_fractions = fires_manager.get_config_value('timeprofile', 'daily_hourly_fractions')
    fires_manager.processed(__name__, __version__,
        timeprofile_version=timeprofile.__version__)
    try:
        for fire in fires_manager.fires:
            _validate_fire(fire)
            for fb in fire.fuelbeds:
                fb['profiled_emissions'] = []
            for g in fire.growth:
                profiler = StaticTimeProfiler(g['start'], g['end']
                    daily_hourly_fractions=daily_hourly_fractions)
                g['hourly_fractions'] = profiler.hourly_fractions
                for fb in fire.fuelbeds:
                    emissions = fb['emissions'] # TODO: multiple
                    tpe = profiler.profile()
                    # TODO: where to put time profiled emissions


    except InvalidDailyHourlyFractionsError, e:
        raise BlueSkyConfigurationError(
            "Invalid timeprofile daily hourly fractions: '{}'".format(e.message))
    except InvalidStartEndTimesError, e:
        raise BlueSkyConfigurationError(
            "Invalid timeprofile start end times: '{}'".format(e.message))
    # except InvalidEmissionsDataError, e:
    #     TODO: do anything with InvalidEmissionsDataError?
    #     raise

    fires_manager.summarize(daily_hourly_fractions=profiler.daily_hourly_fractions)

def _validate_fire(fire):
    if 'growth' not in fire:
        raise ValueError(
            "Missing growth data required for computing timeprofile")
    # TODO: make sure each growth object is valid (and make sure 'pct'
    # add up to 100% ?)
    if 'fuelbeds' not in fire:
        raise ValueError(
            "Missing fuelbed data required for computing timeprofile")
    for fb in fire.fuelbeds:
        if 'emissions' not in fb:
            raise ValueError(
                "Missing emissions data required for computing timeprofile")
