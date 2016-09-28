"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky import  locationutils


class TestLatLng:

    def test_invalid(self):
        expected_err_msg = ("Invalid location data required for "
            "determining single lat/lng for fire")
        with raises(ValueError) as e_info:
            locationutils.LatLng(None)
        assert e_info.value.args[0] == expected_err_msg
        with raises(ValueError) as e_info:
            locationutils.LatLng(1)
        assert e_info.value.args[0] == expected_err_msg
        with raises(ValueError) as e_info:
            locationutils.LatLng("SDFSDF")
        assert e_info.value.args[0] == expected_err_msg

    def test_insufficient(self):
        expected_err_msg = ("Insufficient location data required "
            "for determining single lat/lng for location")
        with raises(ValueError) as e_info:
            locationutils.LatLng({})
        assert e_info.value.args[0] == expected_err_msg
        with raises(ValueError) as e_info:
            locationutils.LatLng({'latitude': 46.0})
        assert e_info.value.args[0] == expected_err_msg

    def test_single_lat_lng(self):
        latlng = locationutils.LatLng({
            "utc_offset": "-07:00",
            "longitude": -119.7615805,
            "area": 10000,
            "ecoregion": "western",
            "latitude": 37.909644
        })
        assert latlng.latitude == 37.909644
        assert latlng.longitude == -119.7615805

    def test_perimeter(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [-121.4522115, 47.4316976],
                            [-121.3990506, 47.4316976],
                            [-121.3990506, 47.4099293],
                            [-121.4522115, 47.4099293],
                            [-121.4522115, 47.4316976]
                        ]
                    ]
                ]
            },
            "ecoregion": "southern",
            "state": "KS",
            "country": "USA",
            "slope": 20.0,
            "elevation": 2320.0,
            "max_humid": 70.0,
            "utc_offset": "-07:00"
        })
        assert latlng.latitude == 47.4316976
        assert latlng.longitude == -121.4522115
