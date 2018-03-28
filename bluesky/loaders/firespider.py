"""bluesky.loaders.firespider
"""

__author__ = "Joel Dubowy"

import datetime
import json
import os

from . import BaseApiLoader, BaseJsonFileLoader
from bluesky.datetimeutils import parse_datetime, parse_utc_offset
from bluesky.exceptions import BlueSkyConfigurationError

__all__ = [
    'JsonApiLoader',
    'JsonFileLoader'
]

class BaseFireSpiderLoader(object):

    START_AFTER_END_ERROR_MSG = "Start must be before end"

    def _marshal(self, fires, start=None, end=None):
        """Marshals FireSpider data into bsp's internal structure

        FireSpider structure:
            {
                "id": "HMS_sdfsdfsdf",
                "fuel_type": "natural",
                "type": "wildfire",
                "growth": [
                    {
                        "start": "2015-08-09T00:00:00Z",
                        "end": "2015-08-10T00:00:00Z",
                        "location": {
                            "area": 900,
                            "geojson": {
                                "type": "MultiPoint",
                                "coordinates": [
                                    [-120.2, 48.1],
                                    [-120.4, 48.2],
                                    [-120.2, 48.2]
                                ]
                            },
                            "utc_offset": "-07:00"
                        }
                    }
                ],
                "source": "HMS",
                "name": "HMS_sdfsdfsdf"
            }

        The only thing that needs to be done is conversion of 'start'
        and 'end' to local time.
        """
        start = start and parse_datetime(start, 'start')
        end = end and parse_datetime(end, 'end')
        if start and end and start > end:
            raise BlueSkyConfigurationError(self.START_AFTER_END_ERROR_MSG)

        for f in fires:
            growth = f.pop('growth', [])
            f['growth'] = []
            for g in growth:
                # the growth object's 'start' and 'end' will be in UTC;
                # Keep them in UTC to compare with start/end query parameters
                # and then convert to local if growth object is within range
                if g.get('start') and g.get('end'):
                    g['start'] = parse_datetime(g.get('start'), 'start')
                    g['end'] = parse_datetime(g.get('end'), 'end')
                    if self._within_time_range(g, start, end):
                        utc_offset = self._get_utc_offset(g)
                        g['start'] += utc_offset
                        g['end'] += utc_offset
                        f['growth'].append(g)
        return fires

    def _get_utc_offset(self, g):
        utc_offset = g.get('location', {}).get('utc_offset')
        if utc_offset:
            return datetime.timedelta(hours=parse_utc_offset(utc_offset))
        else:
            return datetime.timedelta(0)

    def _within_time_range(self, g, start, end):
        # at this point, we know g['start'] and g['end'] are defined,
        # and they are still in UTC
        return ((not start or g['end'] >= start) and
            (not end or g['start'] <= end ))

class JsonApiLoader(BaseApiLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

    def __init__(self, **config):
        super(JsonApiLoader, self).__init__(**config)
        self._query = config.get('query', {})

        # Convert datetime.date objects to strings
        for k in self._query:
            if isinstance(self._query[k], datetime.date):
                self._query[k] = self._query[k].strftime(
                    self.DATETIME_FORMAT)
                # TODO: if no timezone info, add 'Z' to end of string ?

    def load(self):
        fires = json.loads(self.get(**self._query))['data']
        return self._marshal(fires, start=self._query.get('start'),
            end=self._query.get('end'))

class JsonFileLoader(BaseJsonFileLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def load(self):
        fires_data = super(JsonFileLoader, self).load()
        return self._marshal(fires_data['data'])
