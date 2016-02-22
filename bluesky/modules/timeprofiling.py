"""bluesky.modules.timeprofiling"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import copy
import timeprofile
from timeprofile.static import (
    StaticTimeProfiler,
    InvalidHourlyFractionsError,
    InvalidStartEndTimesError,
    InvalidEmissionsDataError
)

from bluesky.datetimeutils import parse_datetimes
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
    hourly_fractions = fires_manager.get_config_value('timeprofiling', 'hourly_fractions')

    fires_manager.processed(__name__, __version__,
        timeprofile_version=timeprofile.__version__)
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            try:
                _run_fire(hourly_fractions, fire)
            except InvalidHourlyFractionsError, e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofiling hourly fractions: '{}'".format(e.message))
            except InvalidStartEndTimesError, e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofiling start end times: '{}'".format(e.message))
            # except InvalidEmissionsDataError, e:
            #     TODO: do anything with InvalidEmissionsDataError?
            #     raise

def _run_fire(hourly_fractions, fire):
    if (hourly_fractions and len(fire.growth) > 1 and
            set([len(e) for p,e in hourly_fractions.items()]) != set([24])):
        # TODO: Support this scenario, but make sure
        # len(hourly_fractions) equals the total number of hours
        # represented by all growth objects, and pass the appropriate
        # slice into each instantiation of StaticTimeProfiler
        # (or build this into StaticProfiler???)
        raise BlueSkyConfigurationError("Only 24-hour repeatable time "
            "profiles supported for fires with multiple growth windows")

    _validate_fire(fire)
    for g in fire.growth:
        tw = parse_datetimes(g, 'start', 'end')
        profiler = StaticTimeProfiler(tw['start'], tw['end'],
            hourly_fractions=hourly_fractions)
        # convert timeprofile to dict with dt keys
        g['timeprofile'] = {}
        fields = profiler.hourly_fractions.keys()
        for i in range(len(profiler.hourly_fractions.values()[0])): # each phase should have same len
            hr = profiler.start_hour + (i * profiler.ONE_HOUR)
            g['timeprofile'][hr.isoformat()] = {
                p: profiler.hourly_fractions[p][i] for p in fields }


def _scale_emissions(data, pct):
    for k in data:
        if isinstance(data[k], dict):
            _scale_emissions(data[k], pct)
        else:
            data[k] = [e * pct/100.0 for e in data[k]]

# Allow summed growth percentages to be between 99.5% and 100.5%
# TODO: Move to common constants module? (fuelbeds defines constant for
# total fuelbeds percentage)
TOTAL_PCT_THRESHOLD = 0.5

def _validate_fire(fire):
    if 'growth' not in fire:
        raise ValueError("Missing growth data required for time profiling")
    for g in fire.growth:
        if 'start' not in g or 'end' not in g or 'pct' not in g:
            raise ValueError(
                "Insufficient growth data required for time profiling")
    if TOTAL_PCT_THRESHOLD < abs(100.0 - reduce(lambda a, b: a + b, [g['pct'] for g in fire.growth])):
        raise RuntimeError(
            "Growth percentages don't add up to 100% - {}".format(fire.growth))
