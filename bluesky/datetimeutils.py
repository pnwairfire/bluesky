"""bluesky.datetimeutils

TODO: Move this module to pyairfire
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__all__ = [
    'parse_datetimes'
]

from pyairfire.datetime import parsing as datetime_parsing

def parse_datetimes(d, *keys):
    r = {}
    for k in keys:
        try:
            r[k] = datetime_parsing.parse(d[k])
        except ValueError, e:
            # datetime_parsing will raise ValueError if invalid format
            # reraise wih specific msg
            raise ValueError("Invalid datetime format for '{}' field: {}".format(k, d[k]))
        except KeyError, e:
            raise ValueError("Missing '{}' datetime field".format(k))
    return r
