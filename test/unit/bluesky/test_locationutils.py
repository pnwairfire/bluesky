"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky import  locationutils


class TestLatLng(object):

    def test_invalid_location_data(self):
        with raises(ValueError) as e_info:
            locationutils.LatLng(None)
        assert e_info.value.args[0] == locationutils.INVALID_LOCATION_DATA

        with raises(ValueError) as e_info:
            locationutils.LatLng(1)
        assert e_info.value.args[0] == locationutils.INVALID_LOCATION_DATA

        with raises(ValueError) as e_info:
            locationutils.LatLng("SDFSDF")
        assert e_info.value.args[0] == locationutils.INVALID_LOCATION_DATA

    def test_no_location_info(self):
        active_area = {
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00"
        }
        with raises(ValueError) as e_info:
            locationutils.LatLng(active_area)
        assert e_info.value.args[0] == locationutils.MISSING_LOCATION_INFO


class TestLatLngActiveArea(object):

    def test_active_area_with_specified_points_missing_lat_lng_info(self):
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

    def test_active_area_with_perimeter_invalid_coordinates(self):
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


    def test_active_area_with_single_specified_point(self):
        latlng = locationutils.LatLng({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0}
            ]
        })
        assert latlng.latitude == 45.0
        assert latlng.longitude == -120.0

    def test_active_area_with_two_specified_points(self):
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

    def test_active_area_with_perimeter(self):
        latlng = locationutils.LatLng({
            "perimeter": {
                "polygon": [
                    [-100.0, 35.0],
                    [-101.0, 35.0],
                    [-101.0, 31.0],
                    [-99.0, 31.0],
                    [-100.0, 35.0]
                ]
            }
        })
        assert latlng.latitude == 33
        assert latlng.longitude == -100.25

    def test_active_area_with_specified_points_and_perimeter(self):
        latlng = locationutils.LatLng({
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                {'area': 20, 'lat': 35.0, 'lng': -121.0}
            ],
            "perimeter": {
                "polygon": [
                    [-100.0, 35.0],
                    [-101.0, 35.0],
                    [-101.0, 31.0],
                    [-99.0, 31.0],
                    [-100.0, 35.0]
                ]
            }
        })
        assert latlng.latitude == 40.0
        assert latlng.longitude == -120.5


class TestLatLngSpecifiedPoint(object):

    def test_specified_point_missing_lat_lng_info(self):
        sp = {'lng': -120.0}  # missing 'lat'
        with raises(ValueError) as e_info:
            locationutils.LatLng(sp)
        assert e_info.value.args[0] == locationutils.MISSING_LOCATION_INFO

    def test_specified_point_invalid_lat_lng_info(self):
        sp = {'lat': 23.0, 'lng': "SDF"} # invalid lng
        with raises(ValueError) as e_info:
            locationutils.LatLng(sp)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT

    def test_valid_specified_point(self):
        latlng = locationutils.LatLng({'area': 34, 'lat': 45.0, 'lng': -120.0})
        assert latlng.latitude == 45.0
        assert latlng.longitude == -120.0


class TestLatLngPerimeter(object):

    def test_perimeter_missing_coordinates(self):
        with raises(ValueError) as e_info:
            locationutils.LatLng({})
        assert e_info.value.args[0] == locationutils.MISSING_LOCATION_INFO

    def test_perimeter_invalid_coordinates(self):
        perimeter =  {
                "polygon": [
                    ["SDF", 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }

        with raises(ValueError) as e_info:
            locationutils.LatLng(perimeter)
        assert e_info.value.args[0] == locationutils.MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER

    def test_valid_perimeter(self):
        latlng = locationutils.LatLng({
            "polygon": [
                [-100.0, 35.0],
                [-101.0, 35.0],
                [-101.0, 31.0],
                [-99.0, 31.0],
                [-100.0, 35.0]
            ]
        })
        assert latlng.latitude == 33
        assert latlng.longitude == -100.25
