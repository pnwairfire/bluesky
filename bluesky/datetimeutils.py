"""bluesky.datetimeutils

TODO: Remove this module and update all imports of this module to import
  from pyairfire.datetime.parsing directly
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

from pyairfire.datetime.parsing import (
    parse_datetime,
    parse_datetimes,
    parse_utc_offset,
    is_round_hour
)
