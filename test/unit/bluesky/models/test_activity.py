"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.models import activity


##
## Tests for TestLocation
##

class TestLocation(object):

    def test_without_active_area(self):
        loc = activity.Location({
            "a": 1
        })

        assert "b" not in loc
        with raises(KeyError) as e_info:
            loc["b"]
        assert loc.get("b") == None
        assert loc.get("b", "foo") == "foo"

        assert "a" in loc
        assert loc["a"] == 1
        assert loc.get("a") == 1
        assert loc.get("a", "foo") == 1

        assert loc == {"a": 1}

    def test_with_active_area(self):
        active_area = {
            "c": 23,
            "fuelbeds": "foo",
            "emissions": "bar",
            "d": 1234
        }
        loc = activity.Location({
            "fuelbeds": 123,
            "a": 1,
            "d": 321
        }, active_area=active_area)

        # "b" is in neither
        assert "b" not in loc
        with raises(KeyError) as e_info:
            loc["b"]
        assert loc.get("b") == None
        assert loc.get("b", "foo") == "foo"

        # a is only in location object
        assert "a" in loc
        assert loc["a"] == 1
        assert loc.get("a") == 1
        assert loc.get("a", "foo") == 1

        # c is only in active area object
        assert "c" in loc
        assert loc["c"] == 23
        assert loc.get("c") == 23
        assert loc.get("c", "foo") == 23

        # "d" is defined in both location and active area;
        # should return value in location object
        assert "d" in loc
        assert loc["d"] == 321
        assert loc.get("d") == 321
        assert loc.get("d", "foo") == 321

        # "fuelbeds" and "emissions" are excluded from looking in parent
        # active area object, so key error if only in active area
        assert "fuelbeds" in loc
        assert loc["fuelbeds"] == 123
        assert loc.get("fuelbeds") == 123
        assert loc.get("fuelbeds", "foo") == 123
        assert "emissions" not in loc
        with raises(KeyError) as e_info:
            loc["emissions"]
        assert loc.get("emissions") == None
        assert loc.get("emissions", "foo") == "foo"

        assert loc == {"a": 1, "d": 321, "fuelbeds": 123}


##
## Tests for ActiveArea
##

class TestActiveAreaLocations(object):

    def test_no_location_info(self):
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00"
            # No location information
        })
        with raises(ValueError) as e_info:
            aa.locations
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_LOCATION_INFO_MSG
        with raises(ValueError) as e_info:
            aa['locations']
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_LOCATION_INFO_MSG

    def test_invalid_specified_points(self):
        # only point missing area
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'lat': 45.0, 'lng': -120.0}, # no area
            ]
        })
        with raises(ValueError) as e_info:
            aa.locations
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']
        with raises(ValueError) as e_info:
            aa['locations']
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']

        # one of two points missing area
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'lat': 35.0, 'lng': -121.0}
            ]
        })
        with raises(ValueError) as e_info:
            aa.locations
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']
        with raises(ValueError) as e_info:
            aa['locations']
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']

    def test_invalid_perimeter(self):
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'perimeter': {
                # missing polygon
                "foo": 123
            }
        })
        with raises(ValueError) as e_info:
            aa.locations
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['perimeter']
        with raises(ValueError) as e_info:
            aa['locations']
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['perimeter']

    def test_one_specified_point(self):
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                # Note that string area value will be cast to float
                {'area': '34', 'lat': 45.0, 'lng': -120.0}
            ]
        })
        expected = [
            {'area': 34.0, 'lat': 45.0, 'lng': -120.0}
        ]
        assert aa.locations == expected
        assert aa['locations'] == expected

    def test_two_specified_points(self):
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 34, 'lat': 44.0, 'lng': -119.0}
            ]
        })
        expected = [
            {'area': 34, 'lat': 45.0, 'lng': -120.0},
            {'area': 34, 'lat': 44.0, 'lng': -119.0}
        ]
        assert aa.locations == expected
        assert aa['locations'] == expected

    def test_perimeter(self):
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'perimeter': {
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        })
        expected = [
            {
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        ]
        assert aa.locations == expected
        assert aa['locations'] == expected

    def test_mixed(self):

        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 34, 'lat': 44.0, 'lng': -119.0}
            ],
            'perimeter': {
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        })
        expected = [
            {'area': 34, 'lat': 45.0, 'lng': -120.0},
            {'area': 34, 'lat': 44.0, 'lng': -119.0}
        ]
        assert aa.locations == expected
        assert aa['locations'] == expected


class TestActiveAreaTotalArea(object):

    def test_specified_points_no_area(self):
        with raises(ValueError) as e_info:
            activity.ActiveArea({
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'specified_points': [
                    {'lat': 45.0, 'lng': -120.0}, # no area
                ]
            }).total_area
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_OR_INVALID_AREA_FOR_SPECIFIED_POINT

    def test_specified_points_one_no_area(self):
        with raises(ValueError) as e_info:
            activity.ActiveArea({
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'specified_points': [
                    {'area': 34, 'lat': 44.0, 'lng': -119.0},
                    {'lat': 45.0, 'lng': -120.0} # no area
                ]
            }).total_area
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_OR_INVALID_AREA_FOR_SPECIFIED_POINT

    def test_only_perimeter_no_area(self):
        with raises(ValueError) as e_info:
            activity.ActiveArea({
                "start": "2014-05-27T17:00:00",
                "end": "2014-05-28T17:00:00",
                "perimeter": {
                    "polygon": [
                        [-121.45, 47.43],
                        [-121.39, 47.43],
                        [-121.39, 47.40],
                        [-121.45, 47.40],
                        [-121.45, 47.43]
                    ]
                }
            }).total_area
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_OR_INVALID_AREA_FOR_PERIMIETER

    def test_one_specified_points(self):
        aa = activity.ActiveArea({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0}
            ]
        })
        assert aa.total_area == 34

    def test_two_specified_points(self):
        aa = activity.ActiveArea({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 20, 'lat': 35.0, 'lng': -121.0}
            ]
        })
        assert aa.total_area == 54

    def test_only_perimeter(self):
        aa = activity.ActiveArea({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            "perimeter": {
                "area": 232,
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        })
        assert aa.total_area == 232

    def test_specified_points_and_perimeter(self):
        aa = activity.ActiveArea({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 20, 'lat': 35.0, 'lng': -121.0}
            ],
            "perimeter": {
                "area": 232,
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        })
        assert aa.total_area == 54



##
## Tests for ActivityCollection
##


class TestActivityCollectionActiveAreas(object):

    def test_no_active_areas(self):
        assert [] == activity.ActivityCollection().active_areas

    def test_with_active_areas(self):
        ac = activity.ActivityCollection(active_areas=[
            {
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'specified_points': [
                    {'area': 52, 'lat': 42.0, 'lng': -116.0}
                ],

            },
            {}
        ])
        expected = [
            {
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'specified_points': [
                    {'area': 52, 'lat': 42.0, 'lng': -116.0}
                ],

            },
            {}
        ]
        assert expected == ac.active_areas


class TestActivityCollectionLocations(object):

    def test_no_active_areas(self):
        assert [] == activity.ActivityCollection().locations

    def test_with_active_areas_but_no_locations(self):
        with raises(ValueError) as e_info:
            activity.ActivityCollection(active_areas=[
                activity.ActiveArea({
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                })
            ]).locations
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_LOCATION_INFO_MSG

    # TODO: add error cases, or

    def test_with_active_areas_and_locations(self):
        ac = activity.ActivityCollection({
            "active_areas": [
                {
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'specified_points': [
                        {'area': 34, 'lat': 45.0, 'lng': -120.0},
                        {'area': 34, 'lat': 44.0, 'lng': -119.0}
                    ],
                    'perimeter': {
                        "polygon": [
                            [-121.45, 47.43],
                            [-121.39, 47.43],
                            [-121.39, 47.40],
                            [-121.45, 47.40],
                            [-121.45, 47.43]
                        ]
                    }
                },
                {
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'specified_points': [
                        {'area': 52, 'lat': 42.0, 'lng': -116.0}
                    ],

                },
                {
                    "start": "2014-05-25T17:00:00",
                    "end": "2014-05-26T17:00:00",
                    'perimeter': {
                        "polygon": [
                            [-111.45, 23.43],
                            [-111.39, 23.43],
                            [-111.39, 23.40],
                            [-111.45, 23.40],
                            [-111.45, 23.43]
                        ]
                    }
                }
            ]
        })
        expected = [
            {'area': 34, 'lat': 45.0, 'lng': -120.0},
            {'area': 34, 'lat': 44.0, 'lng': -119.0},
            {'area': 52, 'lat': 42.0, 'lng': -116.0},
            {
                "polygon": [
                    [-111.45, 23.43],
                    [-111.39, 23.43],
                    [-111.39, 23.40],
                    [-111.45, 23.40],
                    [-111.45, 23.43]
                ]
            }
        ]

        assert expected == ac.locations
