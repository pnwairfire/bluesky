"""bluesky.extrafilewriters
"""

import datetime

import dateutil.tz
from afdatetime import parsing as datetime_parsing

from bluesky.config import Config

def format_utc_offset(utc_offset):
    if hasattr(utc_offset, 'lower'): # is already a string
        return utc_offset
    elif hasattr(utc_offset, 'real'):  # is a number
        # This happens when fire data are loaded from BSF output
        return datetime.datetime(1,1,1,
            tzinfo=dateutil.tz.tzoffset(None, utc_offset*60*60)).strftime('%z')

def format_date_time(ts, utc_offset, csv_file):
    fmt = Config().get('extrafiles', csv_file, 'date_time_format')
    d = datetime_parsing.parse(ts)
    if utc_offset:
        # first, replace '{utc_offset}' with original utc offset string
        fmt = fmt.replace('{utc_offset}', format_utc_offset(utc_offset))
        # next, make 'd' timeaware, incase fmt contains '%z'
        utc_offset = datetime_parsing.parse_utc_offset(utc_offset)
        d = datetime.datetime(d.year, d.month, d.day, d.hour, d.minute,
            d.second, tzinfo=dateutil.tz.tzoffset(None, utc_offset*3600))
    else:
        # TODO: replace with 'Z'?
        fmt = fmt.replace('{utc_offset}', '')
    return d.strftime(fmt)
