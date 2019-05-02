"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.models import activity


##
## Tests for ActiveArea
##


class TestActiveAreaLocations(object):

    def test_no_location_info(self):
        with raises(ValueError) as e_info:
            activity.ActiveArea({
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00"
                # No location information
            }).locations

        assert e_info.value.args[0] == activity.ActiveArea.MISSING_LOCATION_INFO_MSG

    def test_invalid_specified_points(self):
        # only point missing area
        with raises(ValueError) as e_info:
            activity.ActiveArea({
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'specified_points': [
                    {'lat': 45.0, 'lng': -120.0}, # no area
                ]
            }).locations
        assert e_info.value.args[0] == activity.ActiveArea.INVALID_SPECIFIED_POINT_MSG

        # one of two points missing area
        with raises(ValueError) as e_info:
            activity.ActiveArea({
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'specified_points': [
                    {'area': 34, 'lat': 45.0, 'lng': -120.0},
                    {'lat': 35.0, 'lng': -121.0}
                ]
            }).locations
        assert e_info.value.args[0] == activity.ActiveArea.INVALID_SPECIFIED_POINT_MSG

    def test_invalid_perimeter(self):
        with raises(ValueError) as e_info:
             activity.ActiveArea({
                "start": "2014-05-25T17:00:00",
                "end": "2014-05-26T17:00:00",
                'perimeter': {
                    # missing polygon
                    "foo": 123
                }
            }).locations
        assert e_info.value.args[0] == activity.ActiveArea.INVALID_PERIMETER_MSG


    def test_one_specified_point(self):
        aa = activity.ActiveArea({
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0}
            ]
        })
        expected = [
            {'area': 34, 'lat': 45.0, 'lng': -120.0}
        ]
        assert aa.locations == expected

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
## Tests for ActiveArea
##


class TestActivityCollectionActiveAreas(object):


    def test_no_active_areas(self):
        assert [] == activity.ActivityCollection().active_areas

    def test_with_active_areas(self):
        assert [{'a':2},{}] == activity.ActivityCollection(
            active_areas=[{'a':2},{}]).active_areas
