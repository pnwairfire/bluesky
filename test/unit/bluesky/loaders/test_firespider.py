"""Unit tests for bluesky.loaders.firespider
"""

import copy
import datetime

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.loaders import firespider


##
## FireSpider v2
##


FSV2_FIRE_DATA = {
    "source": "goes16",
    "growth_modules": [
        "persistence"
    ],
    "start": "2019-05-09T00:00:00Z",
    "end": "2019-05-14T00:00:00Z",
    "config": {
    },
    "boundary": {
        "south_lat": None,
        "west_lng": None,
        "north_lat": None,
        "east_lng": None
    },
    "count": 841,
    "data": [
        # This is a real GOES-16 fire
        {
            "id": "dc621621-fdc2-4dbd-8178-a6edc77bb632",
            "source": "GOES-16",
            "type": "WF",
            "growth": [
                {
                    "location": {
                        "area": 8290342.812,
                        "geojson": {
                            "type": "Point",
                            "coordinates": [
                                -98.675,
                                23.041
                            ]
                        },
                        "utc_offset": "-06:00"
                    },
                    "start": "2019-02-13T00:00:00",
                    "end": "2019-02-14T00:00:00",
                    "timeprofile": {
                        "2019-02-13T18:00:00": {
                            "area_fraction": 1,
                            "flaming": 1,
                            "smoldering": 1,
                            "residual": 1
                        }
                    },
                    "hourly_frp": {
                        "2019-02-13T18:00:00": 30.14771428571428
                    },
                    "frp": 30.14771428571428
                }
            ]
        },
        {
            "id": "HMS_sdfsdfsdf",
            "source": "HMS",
            "name": "HMS_sdfsdfsdf",
            "fuel_type": "natural",
            "type": "wildfire",
            "growth": [
                {
                    "start": "2015-08-09T00:00:00",
                    "end": "2015-08-10T00:00:00",
                    "timeprofile": {
                        "2015-08-09T00:00:00": {
                            'area_fraction': 0.4118236472945892,
                            'flaming': 0.4118236472945892,
                            'smoldering': 0.4118236472945892,
                            'residual': 0.4118236472945892
                        },
                        "2015-08-09T06:00:00":  {
                            'area_fraction': 0.30661322645290584,
                            'flaming': 0.30661322645290584,
                            'smoldering': 0.30661322645290584,
                            'residual': 0.30661322645290584
                        },
                        "2015-08-10T02:00:00": {
                            'area_fraction': 0.28156312625250507,
                            'flaming': 0.28156312625250507,
                            'smoldering': 0.28156312625250507,
                            'residual': 0.28156312625250507
                        },
                    },
                    "hourly_frp": {
                        "2015-08-09T00:00:00": 47.333333333333336,
                        "2015-08-09T06:00:00":  45.0,
                        "2015-08-10T02:00:00": 53.166666666666664
                    },
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
                },
                {
                    "start": "2015-08-10T00:00:00",
                    "end": "2015-08-11T00:00:00",
                    "location": {
                        "area": 300.0,
                        "geojson": {
                            "type": "MultiPoint",
                            "coordinates": [[-120.2, 48.1]]
                        },
                        "utc_offset": "-07:00"
                    }
                }
            ]
        }
    ]
}
FSV2_FIRE_DATA_MARSHALED = [
    {
        "id": "dc621621-fdc2-4dbd-8178-a6edc77bb632",
        "source": "GOES-16",
        "type": "wildfire",
        "fuel_type": "natural",
        "activity": [
            {
                "active_areas": [
                    {
                        "start": "2019-02-13T00:00:00",
                        "end": "2019-02-14T00:00:00",
                        "frp": 30.14771428571428,
                        "utc_offset": "-06:00",
                        "specified_points": [
                            {
                                "lat": 23.041,
                                "lng":  -98.675,
                                "area": 8290342.812
                            }
                        ],
                        "timeprofile": {
                            "2019-02-13T18:00:00": {
                                "area_fraction": 1,
                                "flaming": 1,
                                "smoldering": 1,
                                "residual": 1
                            }
                        },
                        "hourly_frp": {
                            "2019-02-13T18:00:00": 30.14771428571428
                        }
                    }
                ]
            }
        ]
    },
    {
        "id": "HMS_sdfsdfsdf",
        "source": "HMS",
        "name": "HMS_sdfsdfsdf",
        "fuel_type": "natural",
        "type": "wildfire",
        "activity": [
            {
                "active_areas": [
                    {
                        "start": "2015-08-09T00:00:00",
                        "end": "2015-08-10T00:00:00",
                        "utc_offset": "-07:00",
                        "specified_points": [
                            {
                                "lat": 48.1,
                                "lng": -120.2,
                                "area": 300.0,
                            },
                            {
                                "lat": 48.2,
                                "lng": -120.4,
                                "area": 300.0,
                            },
                            {
                                "lat": 48.2,
                                "lng": -120.2,
                                "area": 300.0,
                            }
                        ],
                        "timeprofile": {
                            "2015-08-09T00:00:00": {
                                'area_fraction': 0.4118236472945892,
                                'flaming': 0.4118236472945892,
                                'smoldering': 0.4118236472945892,
                                'residual': 0.4118236472945892
                            },
                            "2015-08-09T06:00:00":  {
                                'area_fraction': 0.30661322645290584,
                                'flaming': 0.30661322645290584,
                                'smoldering': 0.30661322645290584,
                                'residual': 0.30661322645290584
                            },
                            "2015-08-10T02:00:00": {
                                'area_fraction': 0.28156312625250507,
                                'flaming': 0.28156312625250507,
                                'smoldering': 0.28156312625250507,
                                'residual': 0.28156312625250507
                            },
                        },
                        "hourly_frp": {
                            "2015-08-09T00:00:00": 47.333333333333336,
                            "2015-08-09T06:00:00":  45.0,
                            "2015-08-10T02:00:00": 53.166666666666664
                        }
                    },
                ]
            },
            {
                "active_areas": [
                    {
                        "start": "2015-08-10T00:00:00",
                        "end": "2015-08-11T00:00:00",
                        "utc_offset": "-07:00",
                        "specified_points": [
                            {
                                "lat": 48.1,
                                "lng": -120.2,
                                "area": 300.0
                            }
                        ]
                    }
                ]
            }
        ]
    }
]

class TestBaseFireSpiderLoaderFSV2(object):

    def setup(self):
        pass

    ##
    ## _marshal
    ##

    def _call_marshal(self, fires, start=None, end=None):
        loader = firespider.JsonApiLoader(endpoint="sdf",
            start=start, end=end)
        return loader._marshal(fires)

    def test_marshal_no_start_end(self):
        actual = self._call_marshal(copy.deepcopy(FSV2_FIRE_DATA))
        assert FSV2_FIRE_DATA_MARSHALED == actual

    def test_marshal_w_start(self):
        expected = copy.deepcopy(FSV2_FIRE_DATA_MARSHALED)

        # start is before all activity windows
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-08T:70:00:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-08T00:00:00Z")

        # start is in the middle of first activity window
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-09T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-09T14:00:00Z")

        # start is in the middle of second activity window
        expected[0]['activity'].pop(0)
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-10T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-10T14:00:00Z")

        # start is after all activity windows
        expected = []
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-12T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-12T14:00:00Z")

    def test_marshal_w_end(self):
        expected = copy.deepcopy(FSV2_FIRE_DATA_MARSHALED)

        # end is after all activity windows
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-12T:70:00:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-12T00:00:00Z")

        # start is in the middle of second activity window
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-10T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-10T14:00:00Z")

        # start is in the middle of first activity window
        expected[0]['activity'].pop()
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-09T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-09T14:00:00Z")

        # start is before all activity windows
        expected = []
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-08T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            end="2015-08-08T14:00:00Z")

    def test_marshal_w_start_and_end(self):
        expected = copy.deepcopy(FSV2_FIRE_DATA_MARSHALED)

        # start/end are outside of activity windows
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-08T:70:00:00",
            end="2015-08-12T:70:00:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-08T00:00:00",
            end="2015-08-12T00:00:00Z")

        # start/end are inside, but including all activity windows
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-09T:10:0,0:00",
            end="2015-08-10T:10:0,0:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-09T14:00:00",
            end="2015-08-10T14:00:00Z")

        # start/end are inside first activity window
        expected[0]['activity'].pop()
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-09T:10:0,0:00",
            end="2015-08-10T:10:00:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-09T14:00:00",
            end="2015-08-10T01:00:00Z")

        # exclude all activity windows
        expected = []
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-7T:10:0,0:00",
            end="2015-08-08T:10:00:00")
        assert expected == self._call_marshal(
            copy.deepcopy(FSV2_FIRE_DATA),
            start="2015-08-07T14:00:00",
            end="2015-08-08T01:00:00Z")


        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FSV2_FIRE_DATA),
                start="2015-08-7T:10:0,0:00",
                end="2015-08-4T:10:00:00")
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FSV2_FIRE_DATA),
                start="2015-08-07T14:00:00",
                end="2015-08-04T01:00:00Z")
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
