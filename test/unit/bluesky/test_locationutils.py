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

    def test_geojson_point(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "Point",
                "coordinates": [-121.4522115, 47.4316976]
            }
        })
        assert latlng.latitude == 47.4316976
        assert latlng.longitude == -121.4522115

    def test_geojson_linestring(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "LineString",
                "coordinates": [
                    [100.0, 2.0],
                    [101.0, 1.0]
                ]
            }
        })
        assert latlng.latitude == 2.0
        assert latlng.longitude == 100.0

    def test_geojson_polygon_no_holes(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [100.0, 5.0],
                        [101.0, 0.0],
                        [101.0, 1.0],
                        [100.0, 1.0],
                        [100.0, 5.0]
                    ]
                ]
            }
        })
        assert latlng.latitude == 5.0
        assert latlng.longitude == 100.0

    def test_geojson_polygon_holes(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [100.0, 5.0],
                        [101.0, 0.0],
                        [101.0, 1.0],
                        [100.0, 1.0],
                        [100.0, 5.0]
                    ],
                    [
                        [100.8, 0.8],
                        [100.8, 0.2],
                        [100.2, 0.2],
                        [100.2, 0.8],
                        [100.8, 0.8]
                    ]
                ]
            }
        })
        assert latlng.latitude == 5.0
        assert latlng.longitude == 100.0

    def test_geojson_multi_point(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "MultiPoint",
                "coordinates": [
                    [100.0, 4.5],
                    [101.0, 1.0]
                ]
            }
        })
        assert latlng.latitude == 4.5
        assert latlng.longitude == 100.0

    def test_geojson_multi_linestring(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "MultiLineString",
                "coordinates": [
                    [
                        [100.0, -3.0],
                        [101.0, 1.0]
                    ],
                    [
                        [102.0, 2.0],
                        [103.0, 3.0]
                    ]
                ]
            }
        })
        assert latlng.latitude == -3.0
        assert latlng.longitude == 100.0

    def test_geojson_multi_polygon_one(self):
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

    def test_geojson_multi_polygon_one(self):
        latlng = locationutils.LatLng({
            "geojson": {
                "type": "MultiPolygon",
                "coordinates": [
                    [
                        [
                            [102.0, 2.0],
                            [103.0, 2.0],
                            [103.0, 3.0],
                            [102.0, 3.0],
                            [102.0, 2.0]
                        ]
                    ],
                    [
                        [
                            [100.0, 0.0],
                            [101.0, 0.0],
                            [101.0, 1.0],
                            [100.0, 1.0],
                            [100.0, 0.0]
                        ],
                        [
                            [100.2, 0.2],
                            [100.2, 0.8],
                            [100.8, 0.8],
                            [100.8, 0.2],
                            [100.2, 0.2]
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
        assert latlng.latitude == 2.0
        assert latlng.longitude == 102.0
