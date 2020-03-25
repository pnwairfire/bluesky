import copy
import datetime
import logging

from bluesky.datetimeutils import parse_datetime

def filter_met(met, start, num_hours):
    # the passed-in met is a reference to the fires_manager's met, so copy it
    met = copy.deepcopy(met)

    if not met:
        # return `met` in case it's a dict and dict is expected downstream
        return met

    # limit met to only what's needed to cover time window
    end = start + datetime.timedelta(hours=num_hours)

    # Note: we don't store the parsed first and last hour values
    # because they aren't used outside of this method, and they'd
    # just have to be dumped back to string values when bsp exits
    logging.debug('Determinig met files needed for time window')
    met_files = met.pop('files', [])
    met["files"] = []
    for m in met_files:
        if (parse_datetime(m['first_hour']) <= end
                and parse_datetime(m['last_hour']) >= start):
            met["files"].append(m)
        else:
            logging.debug('Dropping met file %s - not needed for time window',
                m["file"])
    return met
