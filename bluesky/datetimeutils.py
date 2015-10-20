"""bluesky.datetimeutils

TODO: Move this module to pyairfire
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__all__ = [
    'parse_datetimes',
    'parse_utc_offset'
]

import re

from pyairfire.datetime import parsing as datetime_parsing

def parse_datetime(v, k):
    try:
        return datetime_parsing.parse(v)
    except ValueError, e:
        # datetime_parsing will raise ValueError if invalid format
        # reraise wih specific msg
        raise ValueError("Invalid datetime format for '{}' field: {}".format(k, v))

def parse_datetimes(d, *keys):
    r = {}
    for k in keys:
        try:
            r[k] = parse_datetime(d[k], k)
        except KeyError, e:
            raise ValueError("Missing '{}' datetime field".format(k))
    return r

OFFSET_MATCHER = re.compile('([+-]?\d{2}):(\d{2})')
def parse_utc_offset(utc_offset_str):
    """Parses iso8601 formmated utc offset to float value

    Examples:
     > parse_utc_offset('+00:00')
     0.0
     > parse_utc_offset('+04:00')
     4.0
     > parse_utc_offset('-03:30')
     -3.5


    TODO: look at other options:
     - https://bitbucket.org/micktwomey/pyiso8601/
     - https://github.com/dateutil/dateutil/
     - http://labix.org/python-dateutil
     - http://arrow.readthedocs.org/en/latest/
    """
    if not utc_offset_str:
        raise ValueError("UTC offset not defined")
    m = OFFSET_MATCHER.match(utc_offset_str)
    if not m:
        raise ValueError("Invalid UTC offset string format: {}".format(utc_offset_str))
    hours = float(m.group(1))
    minutes = float(m.group(2))
    if hours < -13 or hours > 13 or minutes < 0 or minutes > 59:
        raise ValueError("Invalid UTC offset: {}".format(utc_offset_str))
    hour_fraction = minutes / 60.0
    return (hours - hour_fraction) if (hours < 0) else (hours + hour_fraction)
