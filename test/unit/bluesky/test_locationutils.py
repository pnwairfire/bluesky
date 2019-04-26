"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky import  locationutils


class TestLatLng(object):

    def test_invalid_active_area(self):
        with raises(ValueError) as e_info:
            locationutils.LatLng(None)
        assert e_info.value.args[0] == locationutils.INVALID_ACTIVE_AREA_INFO

        with raises(ValueError) as e_info:
            locationutils.LatLng(1)
        assert e_info.value.args[0] == locationutils.INVALID_ACTIVE_AREA_INFO

        with raises(ValueError) as e_info:
            locationutils.LatLng("SDFSDF")
        assert e_info.value.args[0] == locationutils.INVALID_ACTIVE_AREA_INFO

    def test_no_location_info(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00"
        }
        with raises(ValueError) as e_info:
            locationutils.LatLng(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_LOCATION_INFO_FOR_ACTIVE_AREA

    def test_specified_points_missing_lat_lng_info(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'lat': 23.0, 'lng': "SDF"}, # invalid
            ]
        }
        with raises(ValueError) as e_info:
            locationutils.LatLng(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT

        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'lng': -120.0},  # missing 'lat'
            ]
        }
        with raises(ValueError) as e_info:
            locationutils.LatLng(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT

        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'lat': 23.0}  # missing 'lng'
            ]
        }
        with raises(ValueError) as e_info:
            locationutils.LatLng(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT

    def test_perimeter_invalid_coordinates(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            "perimeter": {
                "polygon": [
                    ["SDF", 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        }
        with raises(ValueError) as e_info:
            locationutils.LatLng(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER


    def test_single_specified_point(self):
        latlng = locationutils.LatLng({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0}
            ]
        })
        assert latlng.latitude == 45.0
        assert latlng.longitude == -120.0

    def test_two_specified_points(self):
        latlng = locationutils.LatLng({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 20, 'lat': 35.0, 'lng': -121.0}
            ]
        })
        assert latlng.latitude == 40.0
        assert latlng.longitude == -120.5

    def test_perimeter(self):
        latlng = locationutils.LatLng({
            "perimeter": {
                "polygon": [
                    [100.0, 5.0],
                    [101.0, 0.0],
                    [101.0, 1.0],
                    [100.0, 1.0],
                    [100.0, 5.0]
                ]
            }
        })
        assert latlng.latitude == 2.4
        assert latlng.longitude == 100.4

    def test_specified_points_and_perimeter(self):
        latlng = locationutils.LatLng({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 20, 'lat': 35.0, 'lng': -121.0}
            ],
            "perimeter": {
                "polygon": [
                    [100.0, 5.0],
                    [101.0, 0.0],
                    [101.0, 1.0],
                    [100.0, 1.0],
                    [100.0, 5.0]
                ]
            }
        })
        assert latlng.latitude == 40.0
        assert latlng.longitude == -120.5



class TestGetTotalActiveArea(object):

    def test_no_location_info(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00"
        }
        with raises(ValueError) as e_info:
            locationutils.get_total_active_area(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_LOCATION_INFO_FOR_ACTIVE_AREA

    def test_specified_points_missing_area(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'lat': 45.0, 'lng': -120.0},
            ]
        }
        with raises(ValueError) as e_info:
            locationutils.get_total_active_area(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_AREA_FOR_SPECIFIED_POINT

        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'lat': 35.0, 'lng': -121.0}
            ]
        }
        with raises(ValueError) as e_info:
            locationutils.get_total_active_area(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_AREA_FOR_SPECIFIED_POINT

    def test_perimeter_missing_area(self):
        active_area = {
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
        }
        with raises(ValueError) as e_info:
            locationutils.get_total_active_area(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_AREA_FOR_PERIMIETER

    def test_only_specified_points(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
            ]
        }
        assert locationutils.get_total_active_area(active_area) == 34

        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 20, 'lat': 35.0, 'lng': -121.0}
            ]
        }
        assert locationutils.get_total_active_area(active_area) == 54

    def test_only_perimeter(self):
        active_area = {
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
        }
        assert locationutils.get_total_active_area(active_area) == 232

    def test_specified_points_and_perimeter(self):
        active_area = {
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
        }
        assert locationutils.get_total_active_area(active_area) == 54
