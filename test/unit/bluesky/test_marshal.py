"""Unit tests for bluesky.loaders.firespider
"""

import copy
import datetime

from bluesky import marshal


NO_GROWTH_FIRE = {
    "id": "dc621621-fdc2-4dbd-8178-a6edc77bb632",
    "source": "GOES-16",
    "type": "WF",
}
NO_GROWTH_FIRE_MARSHALED = {
    "id": "dc621621-fdc2-4dbd-8178-a6edc77bb632",
    "source": "GOES-16",
    "type": "WF",
    "activity": []
}

SIMPLE_MULTI_GROWTH_FIRE = {
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
            "end": "2019-02-14T00:00:00"
        },
        {
            "location": {
                "area": 344.812,
                "latitude": 32.0,
                "longitude": -120.0,
                "utc_offset": "-06:00"
            },
            "start": "2019-02-13T00:00:00",
            "end": "2019-02-14T00:00:00"
        },
        {
            "location": {
                "area": 3000,
                "geojson": {
                    "type": "MultiPolygon",
                    "coordinates": [[[
                        [-121.4522115,47.4316976],
                        [-121.3990506,47.4316976],
                        [-120.3990506,47.4099293],
                        [-121.4522115,47.4099293],
                        [-121.4522115,47.4316976]
                    ]]]
                },
                "utc_offset": "-06:00"
            },
            "start": "2019-02-13T00:00:00",
            "end": "2019-02-14T00:00:00"
        },
        {
            "location": {
                "area": 1000,
                "geojson": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-121.4522115,47.4316976],
                        [-121.3990506,47.4316976],
                        [-120.3990506,47.4099293],
                        [-121.4522115,47.4099293],
                        [-121.4522115,47.4316976]
                    ]]
                },
                "utc_offset": "-06:00"
            },
            "start": "2019-02-13T00:00:00",
            "end": "2019-02-14T00:00:00"
        }
    ]
}
SIMPLE_MULTI_GROWTH_FIRE_MARSHALED = {
    "id": "dc621621-fdc2-4dbd-8178-a6edc77bb632",
    "source": "GOES-16",
    "type": "WF",
    "activity": [
        {
            "active_areas": [
                {
                    "start": "2019-02-13T00:00:00",
                    "end": "2019-02-14T00:00:00",
                    "utc_offset": "-06:00",
                    "specified_points": [
                        {
                            "lat": 23.041,
                            "lng":  -98.675,
                            "area": 8290342.812
                        }
                    ]
                },
            ]
        },
        {
            "active_areas": [
                {
                    "start": "2019-02-13T00:00:00",
                    "end": "2019-02-14T00:00:00",
                    "utc_offset": "-06:00",
                    "specified_points": [
                        {

                            "area": 344.812,
                            "lat": 32.0,
                            "lng": -120.0,
                        }
                    ]
                },
            ]
        },
        {
            "active_areas": [
                {
                    "start": "2019-02-13T00:00:00",
                    "end": "2019-02-14T00:00:00",
                    "utc_offset": "-06:00",
                    "perimeter": {
                        "area": 3000,
                        "polygon": [
                            [-121.4522115,47.4316976],
                            [-121.3990506,47.4316976],
                            [-120.3990506,47.4099293],
                            [-121.4522115,47.4099293],
                            [-121.4522115,47.4316976]
                        ]
                    }
                },
            ]
        },
        {
            "active_areas": [
                {
                    "start": "2019-02-13T00:00:00",
                    "end": "2019-02-14T00:00:00",
                    "utc_offset": "-06:00",
                    "perimeter": {
                        "area": 1000,
                        "polygon":[
                            [-121.4522115,47.4316976],
                            [-121.3990506,47.4316976],
                            [-120.3990506,47.4099293],
                            [-121.4522115,47.4099293],
                            [-121.4522115,47.4316976]
                        ]
                    }
                }
            ]
        }
    ]
}

# This is a GOES-16 fire produced by FireSpider v2
FSV2_GOES16_FIRE = {
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
}
FSV2_GOES16_FIRE_MARSHALED = {
    "id": "dc621621-fdc2-4dbd-8178-a6edc77bb632",
    "source": "GOES-16",
    "type": "WF",
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
}

MULTI_GROWTH_FIRE = {
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
MULTI_GROWTH_FIRE_MARSHALED =     {
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

class TestMarshalBlueskyv4_0To4_1(object):

    def setup(self):
        self.marshaler = marshal.Blueskyv4_0To4_1()

    def test_no_growth_fire(self):
        expected = [NO_GROWTH_FIRE_MARSHALED]
        actual = self.marshaler.marshal([NO_GROWTH_FIRE])
        assert actual == expected

    def test_simple_multi_growth_fire(self):
        expected = [SIMPLE_MULTI_GROWTH_FIRE_MARSHALED]
        actual = self.marshaler.marshal([SIMPLE_MULTI_GROWTH_FIRE])
        assert actual == expected

    def test_fsv2_goes16_fire(self):
        expected = [FSV2_GOES16_FIRE_MARSHALED]
        actual = self.marshaler.marshal([FSV2_GOES16_FIRE])
        assert actual == expected

    def test_multi_growth_fire(self):
        expected = [MULTI_GROWTH_FIRE_MARSHALED]
        actual = self.marshaler.marshal([MULTI_GROWTH_FIRE])
        assert actual == expected

    def test_miltiple_fires(self):
        expected = [
            NO_GROWTH_FIRE_MARSHALED,
            SIMPLE_MULTI_GROWTH_FIRE_MARSHALED,
            FSV2_GOES16_FIRE_MARSHALED,
            MULTI_GROWTH_FIRE_MARSHALED,
        ]
        actual = self.marshaler.marshal([
            NO_GROWTH_FIRE,
            SIMPLE_MULTI_GROWTH_FIRE,
            FSV2_GOES16_FIRE,
            MULTI_GROWTH_FIRE,
        ])
        assert actual == expected
