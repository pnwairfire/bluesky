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


DATETIME_WILDCARD_MATCHER = re.compile(r'{(today|yesterday)([-+]{1}[0-9]+)?(:(?P<format_string>[^}]+))?}')
DEFAULT_DATE_FORMAT_STRING = '%Y%m%d'
def fill_in_datetime_strings(val, today=None):
    """Replaces strftime control codes and special wildcards if input is a string

    Notes:
     - 'today' defaults to current day in GMT
     - 'yesterday' is the day prior to 'today'
     - strftime control codes ('%Y', '%m', etc.) not wrapped in '{today:' + '}'
       are replaced using 'today'

    TODO:
     - rename this method ?
    """
    if hasattr(val, 'lower'):
        today = today or today_utc()
        yesterday = today - ONE_DAY

        while True:
            m = DATETIME_WILDCARD_MATCHER.search(val)
            if not m:
                break

            offset = m.group(2) and int(m.group(2))
            pattern = m.group(4) or DEFAULT_DATE_FORMAT_STRING
            day = (today - ONE_DAY) if (m.group(1) == 'yesterday') else today
            if offset:
                day = day + datetime.timedelta(days=int(offset))

            val = val.replace(m.group(0), day.strftime(pattern))

        # Note: At this point, we used to format all remaining datetime control
        # codes ('%Y', '%m', etc.) outside of '{(today|tomorrow):' + '}' using
        # 'today':
        #    > val = today.strftime(val)
        # This was removed to avoid confusion caused by unintended conversions
        # (such as when '%Y' or other codes happen to be part of config settings.)

    # return val, wether it was modified or not
    return val

_TO_DATETIME_EXTRA_FORMATS = [
    '%Y%m%dT%H:%M:%S', '%Y%m%dT%H:%M:%SZ',
    # TODO: do these last two cause any problems?  The reason to include them is
    #  so that you can, for e.g., specify '{today}12Z' for dispersion start time
    '%Y%m%dT%H', '%Y%m%dT%HZ'
]
# VALID_DATETIME_RANGE is arbitraily defined, but prevents things like
# '444444' being interpreted as datetime.datetime(4444, 4, 4, 0, 0)
VALID_DATETIME_RANGE = (
    # beginning of unix epoch
    datetime.datetime(1970, 1, 1),
    # 100 years from now
    datetime.datetime.now() + datetime.timedelta(days=1) * 360 * 100
)
def to_datetime(val, limit_range=False):
    """Returns date[time] object represented by string
    """
    # the preceeding '_' in '_val' isn't necessary given scoping rules,
    # but it's there to avoid confusion
    def _invalid(_val):
        raise BlueSkyDatetimeValueError(
            "Invalid datetime string value: {}".format(_val))

    if val is not None:
        if isinstance(val, datetime.date):
            return val
        elif hasattr(val, 'lower'):
            try:
                dt = parse_dt(val, extra_formats=_TO_DATETIME_EXTRA_FORMATS)
                # sanity check:
                if limit_range and (dt < VALID_DATETIME_RANGE[0]
                        or dt > VALID_DATETIME_RANGE[1]):
                    _invalid(val + ' (outside of valid range)')
                return dt
            except ValueError, e:
                _invalid(val)
        else:
            _invalid(val)

    # else, it just returns None, val's value
