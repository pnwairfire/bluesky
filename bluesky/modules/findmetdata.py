"""bluesky.modules.findmetdata

This module finds met data files to use for a particular domain and time window
spanning all fire activity periods.
"""

__author__ = "Joel Dubowy"

import datetime
import logging

from met.arl import arlfinder

from bluesky import io
from bluesky.config import Config
from bluesky.datetimeutils import (
    parse_datetimes, is_round_hour, parse_utc_offset, to_datetime
)
from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """runs the findmetdata module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    fires_manager.processed(__name__, __version__)

    # TODO: For playground, there will be only one file containing data for
    # any particular hour.  Allow config to specify using simplified logic
    # for this scenario.  Otherwise, use more complicated logic in
    # arlfinder.ArlFinder (or put both code paths in ArlFinder?)

    met_finder = _get_met_finder(fires_manager)
    time_windows = _get_time_windows(fires_manager)

    wait_config = Config().get('findmetdata','wait')
    @io.wait_for_availability(wait_config)
    def _find():
        files = []
        for time_window in time_windows:
            logging.debug("Findmetdata time window: %s to %s",
                time_window['start'], time_window['end'])
            files.extend(met_finder.find(
                time_window['start'], time_window['end']).get('files', []))

        if not files:
            raise BlueSkyUnavailableResourceError("No met files found")

        return files

    fires_manager.met = {"files": _find()}


def _get_met_root_dir(fires_manager):
    # Note: ArlFinder will raise an exception if met_root_dir is undefined
    # or is not a valid directory
    # TODO: specify domain instead of met_root_dir, and somehow configure (not
    # in the code, since this is open source), per domain, the root dir, arl file
    # name pattern, etc.
    met_root_dir = Config().get('findmetdata', 'met_root_dir')
    if not met_root_dir:
        raise BlueSkyConfigurationError("Config setting 'met_root_dir' "
            "required by findmetdata module")
    logging.debug("Met root dir: %s", met_root_dir)
    return met_root_dir

MET_FINDERS = {
    "arl": arlfinder.ArlFinder
}

def _get_met_finder(fires_manager):
    met_format = Config().get('findmetdata', 'met_format').lower()

    finder_klass = MET_FINDERS.get(met_format)
    if not finder_klass:
        raise BlueSkyConfigurationError(
            "Invalid or unsupported met data format: '{}'".format(met_format))

    met_config = Config().get('findmetdata', met_format)
    logging.debug("%s config: %s", met_format, met_config)

    met_root_dir = _get_met_root_dir(fires_manager)
    return finder_klass(met_root_dir, **met_config)

## Time windows

def _get_time_windows(fires_manager):
    time_windows = [
        _get_configured_time_windows(fires_manager),
        _get_dispersion_time_window(fires_manager)
    ] + _infer_time_windows_from_fires(fires_manager)
    time_windows = [tw for tw in time_windows
        if tw and tw.get('start') and tw.get('end')]
    if not time_windows:
        raise BlueSkyConfigurationError(
            "Start and end times required for finding met data. They"
            "wheren't specied and couldn't be inferred from the fire "
            "and configuration data.")

    return _merge_time_windows(time_windows)

def _get_configured_time_windows(fires_manager):
    time_window = Config().get('findmetdata', 'time_window')
    if time_window:
        logging.debug("Met time window specified in the config")
        time_window = parse_datetimes(time_window, 'first_hour', 'last_hour')
        # met data finder doesn't require round hours, but ....
        if (not is_round_hour(time_window['first_hour']) or
                not is_round_hour(time_window['last_hour'])):
            raise BlueSkyConfigurationError(
                "Met first and last hours must be round hours")
        time_window = {
            'start': time_window['first_hour'],
            'end': time_window['last_hour'] # TODO: round this up to the next hour?
        }
        return time_window

def _infer_time_windows_from_fires(fires_manager):
    time_windows = []

    if fires_manager.fires:
        logging.debug("Met time window determined from fire activity data")
        # Find earliest and latest datetimes that include all fire activity periods
        # TODO: be more intelligent with possible gaps, so that met files for times
        #  when no fire is growing are excluded ?
        for fire in fires_manager.fires:
            with fires_manager.fire_failure_handler(fire):
                for aa in fire.active_areas:
                    # TODO: Because of the following:
                    #   a) start, end, & utc_offset are allowed to be set
                    #      per specified point or perimeter rather than per
                    #      active area, and
                    #   b) accessing [perim|sp].[start|end|utc_offset] will fallback
                    #      on aa's values if not defined in the sp,perim,
                    #  then maybe we should iterate through the aa's locations (sp,perim)
                    #  and execute the following logic on each location. We'd need to
                    #  make sure that time window merging and other downstream logic
                    #  aren't broken or negatively affected.
                    utc_offset = parse_utc_offset(aa.get('utc_offset'))
                    offset = datetime.timedelta(hours=utc_offset)
                    tw = parse_datetimes(aa, 'start', 'end')
                    if tw['start'] > tw['end']:
                        raise ValueError("Invalid activity time window - start: {}, end: {}".format(
                            tw['start'], tw['end']))
                    start = tw['start'] - offset
                    end = tw['end'] - offset
                    time_windows.append({'start': start, 'end': end})

    return time_windows


def _get_dispersion_time_window(fires_manager):
    start = Config().get('dispersion', 'start')
    num_hours = Config().get('dispersion', 'num_hours')
    if start and num_hours:
        return {
            'start': start,
            'end': start + datetime.timedelta(hours=num_hours)
        }

def _merge_time_windows(time_windows):
    merged_time_windows = []
    for tw in sorted(time_windows, key=lambda e: e['start']):
        if (not merged_time_windows
                or merged_time_windows[-1]['end']< tw['start']):
            merged_time_windows.append(tw)
        elif merged_time_windows[-1]['end'] < tw['end']:
            merged_time_windows[-1]['end'] = tw['end']

    return merged_time_windows
