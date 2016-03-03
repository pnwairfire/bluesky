"""Unit tests for bluesky.modules.ingestion"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import copy

from py.test import raises

from bluesky.modules import ingestion

class TestIngester(object):

    def setup(self):
        self.ingester = ingestion.FireIngester()

    ##
    ## Tests For ingest
    ##

    def test_fire_missing_required_fields(self):
        with raises(ValueError) as e:
            self.ingester.ingest({})

        # location must have perimeter or lat+lng+area
        with raises(ValueError) as e:
            self.ingester.ingest({"location": {}})

    def test_fire_with_invalid_growth(self):
        # If growth is specified, each object in the array must have
        # 'start', 'end', and 'pct' defined
        with raises(ValueError) as e:
            self.ingester.ingest(
                {
                    "location": {
                        "perimeter": {
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
                        "ecoregion": "southern"
                    },
                    "growth": [
                        {
                            "sdf": 1
                        }
                    ]
                }
            )

    def test_fire_with_minimum_fields(self):
        f = {
            "location": {
                "perimeter": {
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
                }
            }
        }
        expected = {
            'location': copy.deepcopy(f['location'])
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_fire_with_maximum_optional_fields(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_of": {
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            "location": {
                "perimeter": {
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
                "ecoregion": "southern"
            },
            "growth": [{
                "start": "20150120",
                "end": "20150120",
                "pct": 100.0
            }]
        }
        expected = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            'location': copy.deepcopy(f['location']),
            'growth': copy.deepcopy(f['growth'])
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_flat_fire(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            "perimeter": {
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
            "start": "20150120",
            "end": "20150120",
            "utc_offset": "-07:00"
        }
        expected = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            'location': {
                "perimeter": {
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
                "utc_offset": "-07:00"
            },
            'growth': [
                {
                    "pct": 100.0,
                    "start": "20150120",
                    "end": "20150120"
                }
            ]
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_flat_and_nested_fire(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            "location": {
                "perimeter": {
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
                }
            },
            "ecoregion": "southern",
            "growth": [
                {
                    "start": "20150120",
                    "end": "20150120",
                    "pct": 100.0
                }
            ],
            "meta": {
                "foo": "bar"
            },
            "utc_offset": "-07:00"
        }
        expected = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            'location': {
                "perimeter": {
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
                "utc_offset": "-07:00"
            },
            "growth": [
                {
                    "start": "20150120",
                    "end": "20150120",
                    "pct": 100.0
                }
            ],
            "meta": {
                "foo": "bar"
            }
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_fire_with_ignored_fields(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            "location": {
                "perimeter": {
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
                "foo": "bar"
            },
            "growth": [
                {
                    "start": "20150120",
                    "end": "20150120",
                    "pct": 100.0
                }
            ],
            "bar": "baz"
        }
        expected = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            'location': copy.deepcopy(f['location']),
            'growth': copy.deepcopy(f['growth'])
        }
        expected['location'].pop('foo')
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_fire_with_perimeter_and_lat_lng(self):
        f = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            "location": {
                "perimeter": {
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
                "longitude": -77.379,
                "latitude": 25.041,
                "area": 200
            }
        }
        expected = {
            "id": "SF11C14225236095807750",
            "event_of":{
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            'location': {
                'perimeter': copy.deepcopy(f['location']['perimeter'])
            }
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_fire_with_old_sf2_date_time(self):
        f = {
            "id": "SF11C14225236095807750",
            "latitude": 47.0,
            "longitude": -122.0,
            "area": 100.0,
            "date_time": '201405290000Z'
        }
        expected = {
            "id": "SF11C14225236095807750",
            "location":{
                "latitude": 47.0,
                "longitude": -122.0,
                "area": 100.0
            },
            "growth":[{
                "start": "2014-05-29T00:00:00",
                "end": "2014-05-30T00:00:00",
                "pct": 100.0
            }]
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input

    def test_fire_with_new_sf2_date_time(self):
        f = {
            "id": "SF11C14225236095807750",
            "latitude": 47.0,
            "longitude": -122.0,
            "area": 100.0,
            "date_time": '201508040000-04:00'
        }
        expected = {
            "id": "SF11C14225236095807750",
            "location": {
                "latitude": 47.0,
                "longitude": -122.0,
                "area": 100.0,
                "utc_offset": "-04:00",
            },
            "growth":[{
                "start": "2015-08-04T00:00:00",
                "end": "2015-08-05T00:00:00",
                "pct": 100.0
            }]
        }
        expected_parsed_input = copy.deepcopy(f)
        parsed_input = self.ingester.ingest(f)
        assert expected == f
        assert expected_parsed_input == parsed_input