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

from bluesky.models.fires import Fire
from . import BaseJsonApiLoader, BaseJsonFileLoader
from bluesky.marshal import Blueskyv4_0To4_1

__all__ = [
    'JsonApiLoader',
    'JsonFileLoader'
]


##
## Loader Classes
##

class BaseFireSpiderLoader(object, metaclass=abc.ABCMeta):

    def _marshal(self, data):
        # TODO: support config setting 'skip_failures'
        # v2 didn't initially have version specified in the output data
        if not data.get('version') or data['version'] == "2.0.0":
            func = Blueskyv4_0To4_1().marshal

        elif data['version'] == "3.0.0":
            # Nothing needs be done; just return fires
            func = lambda fires: [Fire(f) for f in fires]

        else:
            raise NotImplementedError("Support for FireSpider "
                "version %s not implemented", data['version'])

        return func(data.get('data', []))


class JsonApiLoader(BaseFireSpiderLoader, BaseJsonApiLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    pass

class JsonFileLoader(BaseFireSpiderLoader, BaseJsonFileLoader):
    """Loads json formatted fire data from the FireSpider web service
    """

    pass