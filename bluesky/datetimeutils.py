"""bluesky.datetimeutils

TODO: Remove this module and update all imports of this module to import
  from pyairfire.datetime.parsing directly
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

from pyairfire.datetime.parsing import (
    parse_datetime,
    parse_datetimes,
    parse_utc_offset,
    is_round_hour
)

def today_midnight_utc():
    d = datetime.datetime.utcnow()
    return datetime.datetime(d.year, d.month, d.day)

ONE_DAY = datetime.timedelta(days=1)
def yesterday_midnight_utc():
    return today_midnight_utc() - ONE_DAY
