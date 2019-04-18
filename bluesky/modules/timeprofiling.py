"""bluesky.modules.timeprofiling"""

__author__ = "Joel Dubowy"

import copy
import timeprofile
from timeprofile.static import (
    StaticTimeProfiler,
    InvalidHourlyFractionsError,
    InvalidStartEndTimesError,
    InvalidEmissionsDataError
)

from bluesky.config import Config
from bluesky.datetimeutils import parse_datetimes
from bluesky.exceptions import BlueSkyConfigurationError
from functools import reduce

__all__ = [
    'run'
]
__version__ = "0.1.0"

def run(fires_manager):
    """Runs timeprofiling module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    hourly_fractions = Config.get('timeprofiling', 'hourly_fractions')

    fires_manager.processed(__name__, __version__,
        timeprofile_version=timeprofile.__version__)
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            try:
                _run_fire(hourly_fractions, fire)
            except InvalidHourlyFractionsError as e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofiling hourly fractions: '{}'".format(str(e)))
            except InvalidStartEndTimesError as e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofiling start end times: '{}'".format(str(e)))
            # except InvalidEmissionsDataError, e:
            #     TODO: do anything with InvalidEmissionsDataError?
            #     raise

def _run_fire(hourly_fractions, fire):
    if (hourly_fractions and len(fire.activity) > 1 and
            set([len(e) for p,e in hourly_fractions.items()]) != set([24])):
        # TODO: Support this scenario, but make sure
        # len(hourly_fractions) equals the total number of hours
        # represented by all activity objects, and pass the appropriate
        # slice into each instantiation of StaticTimeProfiler
        # (or build this into StaticProfiler???)
        raise BlueSkyConfigurationError("Only 24-hour repeatable time "
            "profiles supported for fires with multiple activity windows")

    _validate_fire(fire)
    for g in fire.activity:
        tw = parse_datetimes(g, 'start', 'end')
        profiler = StaticTimeProfiler(tw['start'], tw['end'],
            hourly_fractions=hourly_fractions)
        # convert timeprofile to dict with dt keys
        g['timeprofile'] = {}
        fields = list(profiler.hourly_fractions.keys())
        for i in range(len(list(profiler.hourly_fractions.values())[0])): # each phase should have same len
            hr = profiler.start_hour + (i * profiler.ONE_HOUR)
            g['timeprofile'][hr.isoformat()] = {
                p: profiler.hourly_fractions[p][i] for p in fields }

def _validate_fire(fire):
    if 'activity' not in fire:
        raise ValueError("Missing activity data required for time profiling")
    for g in fire.activity:
        if 'start' not in g or 'end' not in g:
            raise ValueError(
                "Insufficient activity data required for time profiling")
