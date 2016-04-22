"""bluesky.datetimeutils

TODO: Remove this module and update all imports of this module to import
  from pyairfire.datetime.parsing directly
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime
import re

from pyairfire.datetime.parsing import (
    parse_datetime,
    parse_datetimes,
    parse_utc_offset,
    is_round_hour,
    parse as parse_dt
)

from bluesky.exceptions import BlueSkyDatetimeValueError

def today_midnight_utc():
    d = datetime.datetime.utcnow()
    return datetime.datetime(d.year, d.month, d.day)

def today_utc():
    return today_midnight_utc().date()

ONE_DAY = datetime.timedelta(days=1)
def yesterday_midnight_utc():
    return today_midnight_utc() - ONE_DAY

def yesterday_utc():
    return yesterday_midnight_utc().date()


TODAY_MATCHER = re.compile(r'{today:(?P<format_string>[^}]+)}')
YESTERDAY_MATCHER = re.compile(r'.*{yesterday:(?P<format_string>[^}]+)}.*')
def fill_in_datetime_strings(val, today=None):
    """Replaces strftime control codes and special wildcards if input is a string

    Notes:
     - 'today' defaults to current day in GMT
     - 'yesterday' is the day prior to 'today'
     - stftime control codes ('%Y', '%m', etc.) are replaced using 'today'

    TODO:
     - rename this method ?
    """
    if hasattr(val, 'lower'):
        today = today or today_utc()
        yesterday = today - ONE_DAY
        val = val.replace('{today}', today.strftime('%Y%m%d'))
        val = val.replace('{yesterday}', yesterday.strftime('%Y%m%d'))
        while True:
            m = YESTERDAY_MATCHER.match(val)
            if not m:
                break
            val = val.replace('{yesterday:' + m.group(1) + '}',
                yesterday.strftime(m.group(1)))
        # for '{today:PATTERN}' just repalce with patterm, since we'll
        # format all remaining patterns with 'today'
        # ('{today:PATTERN}' really isn't necessary, but it's a way to
        #  explicitly show that the datetime control codes should be formatted
        #  with today's date)
        val = TODAY_MATCHER.sub(r'\g<format_string>', val)
        val = today.strftime(val)

    # else, return val as is
    return val

_TO_DATETIME_EXTRA_FORMATS = [
    '%Y%m%dT%H:%M:%S', '%Y%m%dT%H:%M:%SZ',
    # TODO: do these last two cause any problems?  The reason to include them is
    #  so that you can, for e.g., specify '{today}12Z' for dispersion start time
    '%Y%m%dT%H', '%Y%m%dT%HZ'
]
def to_datetime(val):
    """Returns date[time] object represented by string
    """
    def _invalid(final_val):
        raise BlueSkyDatetimeValueError(
            "Invalid datetime string value: {}".format(val))

    if val is not None:
        if isinstance(val, datetime.date):
            return val
        elif hasattr(val, 'lower'):
            try:
                return parse_dt(val,
                    extra_formats=_TO_DATETIME_EXTRA_FORMATS)
            except ValueError, e:
                _invalid(val)
        else:
            _invalid(val)

    # else, it just returns None, val's value
