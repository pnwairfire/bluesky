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

    def __init__(self, **config):
        self._start = self._config.get('start')
        self._end = self._config.get('end')
        self._start = self._start and parse_datetime(self._start, 'start')
        self._end = self._end and parse_datetime(self._end, 'end')
        if self._start and self._end and self._start > self._end:
            raise BlueSkyConfigurationError(self.START_AFTER_END_ERROR_MSG)

    def _marshal(self, fires):
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
                    if self._within_time_range(g):
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

    def _within_time_range(self, g):
        # at this point, we know g['start'] and g['end'] are defined,
        # and they are still in UTC
        return ((not self._start or g['end'] >= self._start) and
            (not self._end or g['start'] <= self._end ))

class JsonApiLoader(BaseApiLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def __init__(self, **config):
        BaseApiLoader.__init__(self, **config)
        BaseFireSpiderLoader.__init__(self, **config)

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

    def load(self):
        fires = json.loads(self.get(**self._query))['data']
        return self._marshal(fires)

class JsonFileLoader(BaseJsonFileLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def __init__(self, **config):
        BaseApiLoader.__init__(self, **config)
        BaseFireSpiderLoader.__init__(self, **config)

    def load(self):
        fires_data = super(JsonFileLoader, self).load()
        return self._marshal(fires_data['data'])
