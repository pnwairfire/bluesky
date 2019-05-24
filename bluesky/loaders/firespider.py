"""bluesky.loaders.firespider


        FireSpider v1 structure:

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

        FiresSpider v2 structure

        ... FILL IN ONCE AVAILABLE ...


"""

__author__ = "Joel Dubowy"

import abc
import datetime
import json
import os

from bluesky.models.fires import Fire
from . import BaseApiLoader, BaseJsonFileLoader
from bluesky.datetimeutils import parse_datetime, parse_utc_offset
from bluesky.marshal import Blueskyv4_0To4_1

__all__ = [
    'JsonApiLoader',
    'JsonFileLoader'
]


##
## Loader Classes
##

class BaseFireSpiderLoader(object, metaclass=abc.ABCMeta):

    def load(self):
        data = self._get_fire_data()
        fires = self._marshal(data)
        return self._prune(fires)

    @abc.abstractmethod
    def _get_fire_data(self):
        raise NotImplementedError("Implemented by child class")

    def _marshal(self, data):
        # v2 didn't initially have version specified in the output data
        if not data.get('version') or data['version'] == "2.0.0":
            func = Blueskyv4_0To4_1().marshal

        elif data['version'] == 3:
            # Nothing needs be done; just return fires
            func = lambda fires: [Fire(f) for f in fires]

        else:
            raise NotImplementedError("Support for FireSpider "
                "version %s not implemented", data['version'])

        return func(data['data'])

    def _prune(self, fires):
        """Filters out activity windows that are outside of time range.
        """
        for fire in fires:
            for a in fire['activity']:
                a['active_areas'] = [aa for aa in a.active_areas
                    if self._within_time_range(aa)]
            fire['activity'] = [a for a in fire['activity'] if a.active_areas]
        fires = [f for f in fires if f['activity']]

        return fires


    def _within_time_range(self, active_area):
        """
        Note that all times in the activity objects (activity 'start'
        and 'end' times, as well as timeprofile and hourly_frp keys)
        are already in local time.
        """
        utc_offset = self._get_utc_offset(active_area)
        if active_area.get('start') and active_area.get('end'):
            # convert to datetime objects in place
            active_area['start'] = parse_datetime(active_area.get('start'), 'start')
            active_area['end'] = parse_datetime(active_area.get('end'), 'end')
            # the activity object's 'start' and 'end' will be in local time;
            # convert them to UTC to compare with start/end query parameters
            utc_start = active_area['start'] - utc_offset
            utc_end = active_area['end'] - utc_offset

            is_within = ((not self._start or utc_end >= self._start) and
                (not self._end or utc_start <= self._end ))

            return is_within

        return False # not necessary, but makes code more readable

    def _get_utc_offset(self, active_area):
        utc_offset = active_area.get('utc_offset')
        if utc_offset:
            return datetime.timedelta(hours=parse_utc_offset(utc_offset))
        else:
            return datetime.timedelta(0)


class JsonApiLoader(BaseFireSpiderLoader, BaseApiLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def _get_fire_data(self):
        return json.loads(self.get(**self._query))


class JsonFileLoader(BaseFireSpiderLoader, BaseJsonFileLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    def _get_fire_data(self):
        return super(JsonFileLoader, self)._load(self._filename)
