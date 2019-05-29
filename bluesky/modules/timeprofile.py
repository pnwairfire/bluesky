"""bluesky.modules.timeprofile"""

__author__ = "Joel Dubowy"

import copy
from timeprofile import __version__ as timeprofile_version
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
__version__ = "0.1.1"

def run(fires_manager):
    """Runs timeprofile module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    hourly_fractions = Config.get('timeprofile', 'hourly_fractions')

    fires_manager.processed(__name__, __version__,
        timeprofile_version=timeprofile_version)
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            try:
                _run_fire(hourly_fractions, fire)
            except InvalidHourlyFractionsError as e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofile hourly fractions: '{}'".format(str(e)))
            except InvalidStartEndTimesError as e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofile start end times: '{}'".format(str(e)))
            # except InvalidEmissionsDataError, e:
            #     TODO: do anything with InvalidEmissionsDataError?
            #     raise

NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS_MSG = ("Only 24-hour repeatable"
    " time profiles supported for fires with multiple activity windows")

def _run_fire(hourly_fractions, fire):
    active_areas =  fire.active_areas
    if (hourly_fractions and len(active_areas) > 1 and
            set([len(e) for p,e in hourly_fractions.items()]) != set([24])):
        # TODO: Support this scenario, but make sure
        # len(hourly_fractions) equals the total number of hours
        # represented by all activity objects, and pass the appropriate
        # slice into each instantiation of StaticTimeProfiler
        # (or build this into StaticProfiler???)
        raise BlueSkyConfigurationError(NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS_MSG)

    _validate_fire(fire)
    for a in active_areas:
        tw = parse_datetimes(a, 'start', 'end')
        profiler = StaticTimeProfiler(tw['start'], tw['end'],
            hourly_fractions=hourly_fractions)
        # convert timeprofile to dict with dt keys
        a['timeprofile'] = {}
        fields = list(profiler.hourly_fractions.keys())
        for i in range(len(list(profiler.hourly_fractions.values())[0])): # each phase should have same len
            hr = profiler.start_hour + (i * profiler.ONE_HOUR)
            a['timeprofile'][hr.isoformat()] = {
                p: profiler.hourly_fractions[p][i] for p in fields }

MISSING_ACTIVITY_AREA_MSG = "Missing activity data required for time profiling"
INSUFFICIENT_ACTIVITY_INFP_MSG = "Insufficient activity data required for time profiling"

def _validate_fire(fire):
    active_areas = fire.active_areas
    if not active_areas:
        raise ValueError(MISSING_ACTIVITY_AREA_MSG)
    for a in active_areas:
        if 'start' not in a or 'end' not in a:
            raise ValueError(INSUFFICIENT_ACTIVITY_INFP_MSG)
