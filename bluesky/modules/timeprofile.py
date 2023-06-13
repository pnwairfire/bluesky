"""bluesky.modules.timeprofile"""

__author__ = "Joel Dubowy"

import copy
import os
from functools import reduce

from pyairfire import osutils
from timeprofile import __version__ as timeprofile_version
from timeprofile.static import (
    StaticTimeProfiler,
    InvalidHourlyFractionsError,
    InvalidStartEndTimesError
)
from timeprofile.feps import FepsTimeProfiler, FireType

from bluesky.config import Config
from bluesky.datetimeutils import parse_datetimes, parse_datetime
from bluesky.exceptions import BlueSkyConfigurationError

from bluesky.timeprofilers import ubcbsffeps

__all__ = [
    'run'
]
__version__ = "0.1.1"

def run(fires_manager):
    """Runs timeprofile module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    t_config = TimeProfileConfig()

    fires_manager.processed(__name__, __version__,
        timeprofile_version=timeprofile_version)
    for fire in fires_manager.fires:
        with fires_manager.fire_failure_handler(fire):
            try:
                _run_fire(t_config, fire)
            except InvalidHourlyFractionsError as e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofile hourly fractions: '{}'".format(str(e)))
            except InvalidStartEndTimesError as e:
                raise BlueSkyConfigurationError(
                    "Invalid timeprofile start end times: '{}'".format(str(e)))


class TimeProfileConfig(dict):

    LAST_HOUR_MUST_FOLLOW_FIRST_HOUR = ("Time window last_hour can't come before first_hour")

    def __init__(self):

        self['hourly_fractions'] = Config().get('timeprofile', 'hourly_fractions')

        self['time_windows'] = {}
        for t in ('rx', 'wf'):
            self['time_windows'][t] = {
                "first_hour": Config().get('timeprofile', 'time_window', t, 'first_hour'),
                "last_hour": Config().get('timeprofile', 'time_window', t, 'last_hour'),
                "num_hours": Config().get('timeprofile', 'time_window', t, 'num_hours'),
            }

            if (self['time_windows'][t]['last_hour'] and self['time_windows'][t]['first_hour']
                    and self['time_windows'][t]['last_hour'] < self['time_windows'][t]['first_hour']):
                raise BlueSkyConfigurationError(self.LAST_HOUR_MUST_FOLLOW_FIRST_HOUR)


NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS_MSG = ("Only 24-hour repeatable"
    " time profiles supported for fires with multiple activity windows")

def _run_fire(t_config, fire):
    active_areas =  fire.active_areas
    if (t_config['hourly_fractions'] and len(active_areas) > 1 and
            set([len(e) for p,e in t_config['hourly_fractions'].items()]) != set([24])):
        # TODO: Support this scenario, but make sure
        # len(t_config['hourly_fractions']) equals the total number of hours
        # represented by all activity objects, and pass the appropriate
        # slice into each instantiation of StaticTimeProfiler
        # (or build this into StaticProfiler???)
        raise BlueSkyConfigurationError(NOT_24_HOURLY_FRACTIONS_W_MULTIPLE_ACTIVE_AREAS_MSG)

    _validate_fire(fire)
    for a in active_areas:
        profiler = _get_profiler(t_config, fire, a)

        # convert timeprofile to dict with dt keys
        a['timeprofile'] = {}
        fields = list(profiler.hourly_fractions.keys())
        for i in range(len(list(profiler.hourly_fractions.values())[0])): # each phase should have same len
            hr = profiler.start_hour + (i * profiler.ONE_HOUR)
            a['timeprofile'][hr.isoformat()] = {
                p: profiler.hourly_fractions[p][i] for p in fields }

def _get_first_and_last_hours(t_config, active_area, fire_type):
    tw = parse_datetimes(active_area, 'start', 'end')

    if fire_type not in t_config['time_windows']:
        return tw['start'], tw['end']
    twc = t_config['time_windows'][fire_type]

    # the first hour will be:
    #  - the configured first hour, if defined
    #  - else, the active ara start hour, tw['start']
    if twc.first_hour:
        first_hour = parse_datetime(twc.first_hour)
    else:
        first_hour = tw['start']


    # The last hour will be:
    #  - the configured last hour, if defined
    #  - else, the first_hour plus the configured number of hours, if defined
    #  - else, the actrive area end hour, tw['end']
    if twc.last_hour:
        last_hour = parse_datetime(twc.last_hour)
    elif twc.num_hours:
        last_hour = first_hour + datetime.timedelta(hours=twc.num_hours)
    else:
        last_hour = tw['end']

    # last_hour will only be after first_hour if a) twc['first_hour'] is not
    # set, b) twc['last_hour'] is set, and twc['last_hour'] is earlier
    # than the active area's start time
    if last_hour < first_hour:
        logging.warn(f"Configured timeprofile period, {last_hour} - {first_hour}, is invalid. "
            f"Using active area start and end, {tw['start']} - {tw['end']}")
        return tw['start'], tw['end']

    return first_hour, last_hour

def _get_profiler(t_config, fire, active_area):
    first_hour, last_hour = _get_first_and_last_hours(t_config, active_area, fire.type)

    # Use FepsTimeProfiler for Rx fires and StaticTimeProfiler for WF,
    # Unless custom hourly_fractions are specified, in which case
    # Static Time Profiler is used for all fires.
    # If ignition_start and ignition_end aren't specified for Rx fires,
    # FepsTimeProfiler will assume 9am-12pm
    # TODO: add config setting to use FEPS for Rx even if custom
    #   hourly_fractions are specified (or the converse - i.e. alwys use
    #   FEPS for rx and add setting to turn on use of hourly_fractions,
    #   if specified, for Rx)
    if fire.type == 'rx' and not t_config['hourly_fractions']:
        ig_start = active_area.get('ignition_start') and parse_datetime(
            active_area['ignition_start'], k='ignition_start')
        ig_end = active_area.get('ignition_end') and parse_datetime(
            active_area['ignition_end'], k='ignition_end')
        # TODO: pass in duff_fuel_load, total_above_ground_consumption,
        #    total_below_ground_consumption, moisture_category,
        #    relative_humidity, wind_speed, and duff_moisture_content,
        #    if defined?
        return FepsTimeProfiler(first_hour, last_hour,
            local_ignition_start_time=ig_start,
            local_ignition_end_time=ig_end,
            fire_type=FireType.RX)

    else:
        model_name = Config().get("timeprofile", "model").lower()
        if model_name == "ubc-bsf-feps":
            wfrtConfig = Config().get('timeprofile', 'ubc-bsf-feps')
            working_dir = wfrtConfig.get('working_dir')
            delete_if_no_error = wfrtConfig.get(
                'delete_working_dir_if_no_error')
            with osutils.create_working_dir(working_dir=working_dir,
                    delete_if_no_error=delete_if_no_error) as wdir:
                fire_working_dir = os.path.join(wdir, "feps-timeprofile-{}".format(fire.id))
                if not os.path.exists(fire_working_dir):
                    os.makedirs(fire_working_dir)
                return ubcbsffeps.UbcBsfFEPSTimeProfiler(active_area,
                    fire_working_dir, wfrtConfig)
        else:
            return StaticTimeProfiler(first_hour, last_hour,
                hourly_fractions=t_config['hourly_fractions'])

MISSING_ACTIVITY_AREA_MSG = "Missing activity data required for time profiling"
INSUFFICIENT_ACTIVITY_INFP_MSG = "Insufficient activity data required for time profiling"

def _validate_fire(fire):
    active_areas = fire.active_areas
    if not active_areas:
        raise ValueError(MISSING_ACTIVITY_AREA_MSG)
    for a in active_areas:
        if 'start' not in a or 'end' not in a:
            raise ValueError(INSUFFICIENT_ACTIVITY_INFP_MSG)
