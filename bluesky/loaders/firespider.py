"""bluesky.loaders.firespider
"""

__author__ = "Joel Dubowy"

import datetime
import json
import os

from . import BaseApiLoader, BaseFileLoader
from bluesky.datetimeutils import parse_datetime, parse_utc_offset

__all__ = [
    'FileLoader'
]

class BaseFireSpiderLoader(object):

    def _marshal(self, fires):
        """Marshals FireSpider data into bsp's internal structure

        FireSpider structure:
            {
                "id": "HMS_sdfsdfsdf",
                "fuel_type": "natural",
                "type": "wildfire",
                "growth": [
                    {
                        "end": "2015-08-10T07:00:00Z",
                        "start": "2015-08-09T07:00:00Z",
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
            for g in f.get('growth', []):
                # 'start' and 'end' will be in UTC; convert to local
                utc_offset = g.get('location', {}).get('utc_offset')
                if utc_offset:
                    utc_offset = parse_utc_offset(utc_offset)
                g['start'] = self._marshal_time(g.get('start'), utc_offset)
                g['end'] = self._marshal_time(g.get('end'), utc_offset)

        return fires

    def _marshal_time(self, t, utc_offset):
        if t:
            t = parse_datetime(t, 'start/end')
            if utc_offset:
                t = t + datetime.timedelta(hours=utc_offset)
            return t
        # else, leave undefined

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
        return self._marshal(fires)

class JsonFileLoader(BaseFileLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

    def load(self):
        fires = self._load_json_file(self._filename)['data']
        return self._marshal(fires)
