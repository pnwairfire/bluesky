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


_TO_DATETIME_EXTRA_FORMATS = [
    '%Y%m%dT%H:%M:%S', '%Y%m%dT%H:%M:%SZ',
    # TODO: do these last two cause any problems?  The reason to include them is
    #  so that you can, for e.g., specify '{today}12Z' for dispersion start time
    '%Y%m%dT%H', '%Y%m%dT%HZ'
]
def to_datetime(val, today=None):
    """Returns date[time] object represented by string

    Notes:
     - 'today' represents the current day in GMT
     - 'yesterday' represents the the day before the currrent day in GMT
     - stftime control codes ('%Y', '%m', etc.) are replaced using current
       GMT day's midnight
    """
    def _invalid(final_val):
        raise BlueSkyDatetimeValueError(
            "Invalid datetime string value: {}".format(val))

    if val is not None:
        today = today or today_utc()
        yesterday = today - ONE_DAY
        if isinstance(val, datetime.date):
            return val
        elif hasattr(val, 'lower'):
            try:
                return parse_dt(val)
            except ValueError, e:
                # try filling in strftime control code as well as any
                # {today} or {yesterday} wild cards
                val = today.strftime(val)
                val = val.replace('{today}', today.strftime('%Y%m%d'))
                val = val.replace('{yesterday}', yesterday.strftime('%Y%m%d'))
                # now, any exception raised by parse_dt will rise up to
                # calling call
                try:
                    return parse_dt(val,
                        extra_formats=_TO_DATETIME_EXTRA_FORMATS)
                except:
                    _invalid(val)
        else:
            _invalid(val)

    # else, it just returns None, val's value
