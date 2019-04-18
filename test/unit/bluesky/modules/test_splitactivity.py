"""Unit tests for bluesky.modules.splitactivity"""

__author__ = "Joel Dubowy"

import copy

from py.test import raises

from bluesky.modules import splitactivity

##
## No activity to split
##

class TestNoActivity(object):

    def test(self):
        fire = FIRE_NO_ACTIVITY = {
            "name": "North fire"
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected


##
## One activity object to split
##

BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY = {
    "name": "North fire",
    "activity": [
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 103.0,
                "ecoregion": "western",
                # lat/lng or geojson geometry to be filled in
                "max_humid": 80,
                "moisture_duff": 100.0,
                "rain_days": 8,
                "snow_month": 5,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        }
    ]
}

class TestOneActivityPreFuelbedsNothingSplit(object):

    def test_lat_lng(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['latitide'] = 47.2
        fire['activity'][0]['location']['longitude'] = 108.2
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

    def test_invalid_geojson(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "SDFZZZ123",
            "coordinates": [
                [-100.0, 34.0],
                [-101.0, 35.4]
            ]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected


    def test_point(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "Point",
            "coordinates": [-102.0, 39.5]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

    def test_line_string(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "LineString",
            "coordinates": [
                [-100.0, 34.0],
                [-101.0, 35.4]
            ]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

    def test_polygon(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
           "type": "Polygon",
           "coordinates": [
                [
                    [-100.0, 34.0], [-101.0, 35.4], [-101.5, 34.4]
                ]
           ]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

    def test_polygon_with_hole(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
           "type": "Polygon",
           "coordinates": [
                [
                    [-100.0, 34.0], [-101.0, 35.4], [-101.5, 34.4]
                ],
                # the hole is ignored in centroid computation
                [
                    [-100.2, 35.2], [-100.3, 34.4], [-100.1, 34.3]
                ]
           ]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

    def test_multi_line_string(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "MultiLineString",
            "coordinates": [
                [
                    [-100.0, 34.0], [-101.0, 35.4]
                ],
                [
                    [-101.5, 34.4]
                ]
            ]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

    def test_multi_polygon_with_area(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-100.0, 34.0], [-101.0, 35.4], [-101.5, 34.4]
                    ],
                    # the hole is ignored in centroid computation
                    [
                        [-100.2, 35.2], [-100.3, 34.4], [-100.1, 34.3]
                    ]
                ],
                [
                    [
                        [-104.1, 34.12], [-102.4, 33.23]
                    ]
                ]
            ]
        }
        # Expect no change, due to not knowing how to divide area
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected

class TestOneActivityPreFuelbeds(object):

    def test_multi_point(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "MultiPoint",
            "coordinates": [
                [-100.0, 34.0],
                [-101.0, 35.4]
            ]
        }
        expected = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        expected['activity'][0]['location']['area'] /= 2
        expected['activity'].append(copy.deepcopy(expected['activity'][0]))
        expected['activity'][0]['location']['geojson'] = {
            "type": "Point",
            "coordinates": [-100.0, 34.0]
        }
        expected['activity'][1]['location']['geojson'] = {
            "type": "Point",
            "coordinates": [-101.0, 35.4]
        }
        splitactivity._split(fire, False)
        assert fire == expected

    def test_multi_point_no_area(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
            "type": "MultiPoint",
            "coordinates": [
                [-100.0, 34.0],
                [-101.0, 35.4]
            ]
        }
        expected = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        expected['activity'][0]['location']['area'] /= 2
        expected['activity'].append(copy.deepcopy(expected['activity'][0]))
        expected['activity'][0]['location']['geojson'] = {
            "type": "Point",
            "coordinates": [-100.0, 34.0]
        }
        expected['activity'][1]['location']['geojson'] = {
            "type": "Point",
            "coordinates": [-101.0, 35.4]
        }
        splitactivity._split(fire, False)
        assert fire == expected

    def test_multi_polygon_no_area(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location'].pop('area')
        fire['activity'][0]['location']['geojson'] = {
            "type": "MultiPolygon",
            "coordinates": [
                [
                    [
                        [-100.0, 34.0], [-101.0, 35.4], [-101.5, 34.4]
                    ],
                    # the hole is ignored in centroid computation
                    [
                        [-100.2, 35.2], [-100.3, 34.4], [-100.1, 34.3]
                    ]
                ],
                [
                    [
                        [-104.1, 34.12], [-102.4, 33.23]
                    ]
                ]
            ]
        }
        expected = copy.deepcopy(fire)
        expected['activity'].append(copy.deepcopy(expected['activity'][0]))
        expected['activity'][0]['location']['geojson'] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-100.0, 34.0], [-101.0, 35.4], [-101.5, 34.4]
                ],
                # the hole is ignored in centroid computation
                [
                    [-100.2, 35.2], [-100.3, 34.4], [-100.1, 34.3]
                ]
            ]
        }
        expected['activity'][1]['location']['geojson'] = {
            "type": "Polygon",
            "coordinates": [
                [
                    [-104.1, 34.12], [-102.4, 33.23]
                ]
            ]
        }
        splitactivity._split(fire, False)
        assert fire == expected


##
## Two Activity Object
##

FIRE_PRE_FUELBEDS_TWO_ACTIVITY = {
    "name": "North fire",
    "activity": [
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 85.0,
                "ecoregion": "western",
                'geojson': {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [-100.0, 34.0], [-101.0, 35.4]
                        ],
                        [
                            [-101.5, 34.4]
                        ]
                    ]
                },
                "max_humid": 80,
                "moisture_duff": 100.0,
                "rain_days": 8,
                "snow_month": 5,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        },
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 15.0,
                "ecoregion": "western",
                'geojson': {
                    "type": "MultiPoint",
                    "coordinates": [
                        [-100.0, 34.0],
                        [-101.0, 35.4],
                        [-102.0, 35.0]
                    ]
                },
                "max_humid": 80,
                "moisture_duff": 75.0,
                "rain_days": 2,
                "snow_month": 4,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        }
    ]
}
EXPECTED_PRE_FUELBEDS_TWO_ACTIVITY = {
    "name": "North fire",
    "activity": [
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 85.0,
                "ecoregion": "western",
                "geojson": {
                    "type": "MultiLineString",
                    "coordinates": [
                        [
                            [-100.0, 34.0], [-101.0, 35.4]
                        ],
                        [
                            [-101.5, 34.4]
                        ]
                    ]
                },
                "max_humid": 80,
                "moisture_duff": 100.0,
                "rain_days": 8,
                "snow_month": 5,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        },
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 5.0,
                "ecoregion": "western",
                'geojson': {
                    "type": "Point",
                    "coordinates": [-100.0, 34.0]
                },
                "max_humid": 80,
                "moisture_duff": 75.0,
                "rain_days": 2,
                "snow_month": 4,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        },
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 5.0,
                "ecoregion": "western",
                'geojson': {
                    "type": "Point",
                    "coordinates": [-101.0, 35.4]
                },
                "max_humid": 80,
                "moisture_duff": 75.0,
                "rain_days": 2,
                "snow_month": 4,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        },
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "location": {
                "area": 5.0,
                "ecoregion": "western",
                'geojson': {
                    "type": "Point",
                    "coordinates": [-102.0, 35.0]
                },
                "max_humid": 80,
                "moisture_duff": 75.0,
                "rain_days": 2,
                "snow_month": 4,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            }
        }
    ]
}

class TestMultipleActivityPreFuelbeds(object):

    def test_mixed_dont_record_orig(self):
        fire = copy.deepcopy(FIRE_PRE_FUELBEDS_TWO_ACTIVITY)
        splitactivity._split(fire, False)
        assert fire == EXPECTED_PRE_FUELBEDS_TWO_ACTIVITY

    def test_mixed_record_orig(self):
        fire = copy.deepcopy(FIRE_PRE_FUELBEDS_TWO_ACTIVITY)
        splitactivity._split(fire, True)
        expected = copy.deepcopy(EXPECTED_PRE_FUELBEDS_TWO_ACTIVITY)
        expected['original_activity'] = FIRE_PRE_FUELBEDS_TWO_ACTIVITY['activity']
        assert fire == expected


##
## Post Fuelbeds
##

FIRE_POST_EMISSIONS = {
    "name": "North fire",
    "activity": [
        {
            "start": "2018-06-18T17:00:00",
            "end": "2018-06-18T19:00:00",
            "consumption": {
                "summary": {
                    "flaming": 974.9004441607276,
                    "residual": 1.0099150000000001,
                    "smoldering": 77.91102586338258,
                    "total": 1053.8213850241102
                }
            },
            "emissions": {
                "summary": {
                    "PM2.5": 8.409888321929879,
                    "total": 8.409888321929879
                }
            },
            "fuelbeds": [
                {
                    "consumption": {},
                    "emissions": {
                        "flaming": {
                            "PM2.5": [7.0972752334901]
                        },
                        "residual": {
                            "PM2.5": [0.016796906280000003]
                        },
                        "smoldering": {
                            "PM2.5": [1.2958161821597791]
                        },
                        "total": {
                            "PM2.5": [8.409888321929879]
                        }
                    },
                    "fccs_id": "0",
                    "heat": {
                        "flaming": [15598407106.571644],
                        "residual": [16158640.000000004],
                        "smoldering": [1246576413.814121],
                        "total": [16861142160.385767]
                    },
                    "pct": 100.0
                }
            ],
            "heat": {
                "summary": {
                    "flaming": 15598407106.571644,
                    "residual": 16158640.000000004,
                    "smoldering": 1246576413.814121,
                    "total": 16861142160.385765
                }
            },
            "location": {
                "area": 103.0,
                "ecoregion": "western",
                "geojson": {
                    "coordinates": [
                        [-118.85,46.188],
                        [-118.80,46.2],
                    ],
                    "type": "MultiPoint"
                },
                "max_humid": 80,
                "max_temp": 30,
                "max_temp_hour": 14,
                "max_wind": 6,
                "max_wind_aloft": 6,
                "min_humid": 40,
                "min_temp": 13,
                "min_temp_hour": 4,
                "min_wind": 6,
                "min_wind_aloft": 6,
                "moisture_duff": 100.0,
                "rain_days": 8,
                "snow_month": 5,
                "sunrise_hour": 5,
                "sunset_hour": 21,
                "utc_offset": "-07:00"
            },
            "timeprofile": {
                "2018-06-18T17:00:00": {
                    "area_fraction": 0.12,
                    "flaming": 0.12,
                    "residual": 0.12,
                    "smoldering": 0.12
                },
                "2018-06-18T18:00:00": {
                    "area_fraction": 0.88,
                    "flaming": 0.88,
                    "residual": 0.88,
                    "smoldering": 0.88
                }
            }
        }
    ]
}

class TestSplitActivityPostFuelbeds(object):

    def test_basic(self):
        fire = copy.deepcopy(BASE_FIRE_PRE_FUELBEDS_ONE_ACTIVITY)
        fire['activity'][0]['location']['geojson'] = {
           "type": "Polygon",
           "coordinates": [
                [
                    [-100.0, 34.0], [-101.0, 35.4], [-101.5, 34.4]
                ]
           ]
        }
        # Expect no change
        expected = copy.deepcopy(fire)
        splitactivity._split(fire, False)
        assert fire == expected
