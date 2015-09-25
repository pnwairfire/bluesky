"""bluesky.modules.timeprofiling"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import timeprofile
from timeprofile.static import (
    StaticTimeProfiler,
    InvalidHourlyFractionsError,
    InvalidStartEndTimesError,
    InvalidEmissionsDataError
)

from pyairfire.datetime import parsing as datetime_parsing

from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'run'
]
__version__ = "0.1.0"

def run(fires_manager):
    """Runs timeprofiling module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    daily_hourly_fractions = fires_manager.get_config_value('timeprofiling', 'daily_hourly_fractions')
    fires_manager.processed(__name__, __version__,
        timeprofile_version=timeprofile.__version__)
    try:
        for fire in fires_manager.fires:
            _validate_fire(fire)
            for fb in fire.fuelbeds:
                fb['profiled_emissions'] = []
            for g in fire.growth:
                # datetime_parsing will raise ValueError if invalid format
                tw = {}
                for k in ['start', 'end']:
                    try:
                        tw[k] = datetime_parsing.parse(g[k])
                    except ValueError, e:
                        # reraise wih specific msg
                        raise ValueError("Invalid datetime format for growth {} field: {}".format(k, g[k]))

                profiler = StaticTimeProfiler(tw['start'], tw['end'],
                    hourly_fractions=daily_hourly_fractions)
                g['hourly_fractions'] = profiler.hourly_fractions
                for fb in fire.fuelbeds:
                    emissions = fb['emissions'] # TODO: multiply each emission by g['pct']
                    tpe = profiler.profile(emissions)
                    fb['profiled_emissions'].append({
                        "start": g["start"],
                        "end": g["end"],
                        "emissions": tpe
                    })


    except InvalidHourlyFractionsError, e:
        raise BlueSkyConfigurationError(
            "Invalid timeprofiling daily hourly fractions: '{}'".format(e.message))
    except InvalidStartEndTimesError, e:
        raise BlueSkyConfigurationError(
            "Invalid timeprofiling start end times: '{}'".format(e.message))
    # except InvalidEmissionsDataError, e:
    #     TODO: do anything with InvalidEmissionsDataError?
    #     raise

    fires_manager.summarize(hourly_fractions=profiler.hourly_fractions)

def _validate_fire(fire):
    if 'growth' not in fire:
        raise ValueError(
            "Missing growth data required for time profiling")
    for g in fire.growth:
        if 'start' not in g or 'end' not in g or 'pct' not in g:
            raise ValueError(
                "Insufficient growth data required for time profiling")
    # TODO: make sure 'pct' add up to 100% ?
    if 'fuelbeds' not in fire:
        raise ValueError(
            "Missing fuelbed data required for time profiling")
    for fb in fire.fuelbeds:
        if 'emissions' not in fb:
            raise ValueError(
                "Missing emissions data required for time profiling")
