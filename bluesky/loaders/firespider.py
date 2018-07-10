"""bluesky.loaders.firespider
"""

__author__ = "Joel Dubowy"

import datetime
import json
import os

from . import BaseApiLoader, BaseJsonFileLoader
from bluesky.datetimeutils import parse_datetime, parse_utc_offset

__all__ = [
    'JsonApiLoader',
    'JsonFileLoader'
]

class BaseFireSpiderLoader(object):

    START_AFTER_END_ERROR_MSG = "Start must be before end"

    def _marshal(self, fires):
        """Marshals FireSpider data into bsp's internal structure

        FireSpider structure:

            {
                "growth_modules": [
                    "persistence"
                ],
                "count": 6,
                "data": [
                    {
                        "source": "GOES-16",
                        "growth": [
                            {
                                "frp": 55.416666666666664,
                                "timeprofile": {
                                    "2018-06-27T20:00:00": {
                                        "residual": 1.0,
                                        "area_fraction": 1.0,
                                        "smoldering": 1.0,
                                        "flaming": 1.0
                                    }
                                },
                                "hourly_frp": {
                                    "2018-06-27T20:00:00": 55.416666666666664
                                },
                                "location": {
                                    "area": 11663.592000000002,
                                    "geojson": {
                                        "coordinates": [
                                            -71.362,
                                            50.632
                                        ],
                                        "type": "Point"
                                    },
                                    "utc_offset": "-04:00"
                                },
                                "end": "2018-06-28T00:00:00",
                                "start": "2018-06-27T00:00:00"
                            }
                        ],
                        "type": "WF",
                        "id": "91736f4b-c013-424a-badb-35fa6a771d5b"
                    },
                    ...,
                ],
                "boundary": {
                    "west_lng": null,
                    "south_lat": null,
                    "north_lat": null,
                    "east_lng": null
                },
                "end": "2018-07-03T00:00:00Z",
                "start": "2018-06-28T00:00:00Z",
                "source": "goes16"
            }

        The only thing that needs to be done is to filter out growth
        windows that are outside of time range. Nothing else needs to
        be done since all times in the growth objects (growth 'start'
        and 'end' times, as well as timeprofile and hourly_frp keys)
        are already in local time.
        """
        for f in fires:
            f['growth'] = [g for g in f.pop('growth', [])
                if self._within_time_range(g)]

        fires = [f for f in fires if f['growth']]

        return fires

    def _within_time_range(self, g):
        utc_offset = self._get_utc_offset(g)
        if g.get('start') and g.get('end'):
            # convert to datetime objects in place
            g['start'] = parse_datetime(g.get('start'), 'start')
            g['end'] = parse_datetime(g.get('end'), 'end')
            # the growth object's 'start' and 'end' will be in local time;
            # convert them to UTC to compare with start/end query parameters
            utc_start = g['start'] - utc_offset
            utc_end = g['end'] - utc_offset

            return ((not self._start or utc_end >= self._start) and
                (not self._end or utc_start <= self._end ))

        return False # not necessary, but makes code more readable

    def _get_utc_offset(self, g):
        utc_offset = g.get('location', {}).get('utc_offset')
        if utc_offset:
            return datetime.timedelta(hours=parse_utc_offset(utc_offset))
        else:
            return datetime.timedelta(0)

class JsonApiLoader(BaseApiLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def load(self):
        fires = json.loads(self.get(**self._query))['data']
        return self._marshal(fires)

class JsonFileLoader(BaseJsonFileLoader, BaseFireSpiderLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def load(self):
        fires_data = super(JsonFileLoader, self).load()
        return self._marshal(fires_data['data'])
