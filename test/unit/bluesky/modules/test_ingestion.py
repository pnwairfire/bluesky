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

    def test_old_sf2_fire(self):
        f = {
            "area": 199.999999503,
            "canopy": "",
            "ch4": "",
            "co": "",
            "co2": "",
            "consumption_duff": "",
            "consumption_flaming": "",
            "consumption_residual": "",
            "consumption_smoldering": "",
            "country": "Unknown",
            "county": "",
            "date_time": "201405290000Z",
            "duff": "",
            "elevation": 0.0,
            "event_id": "SF11E589961",
            "event_url": "http://playground.dri.edu/smartfire/events/bd1af2ca-a09d-4b1b-9135-ac41132d2e49",
            "fccs_number": "",
            "fips": -9999,
            "fuel_100hr": "",
            "fuel_10hr": "",
            "fuel_10khr": "",
            "fuel_1hr": "",
            "fuel_1khr": "",
            "fuel_gt10khr": "",
            "grass": "",
            "heat": "",
            "id": "SF11C99165520788816390",
            "latitude": 26.286,
            "litter": "",
            "longitude": -77.118,
            "max_humid": 80.0,
            "max_temp": 30.0,
            "max_temp_hour": 14,
            "max_wind": 6.0,
            "max_wind_aloft": 6.0,
            "min_humid": 40.0,
            "min_temp": 13.0,
            "min_temp_hour": 4,
            "min_wind": 6.0,
            "min_wind_aloft": 6.0,
            "moisture_100hr": 12.0,
            "moisture_10hr": 12.0,
            "moisture_1hr": 10.0,
            "moisture_1khr": 22.0,
            "moisture_duff": 150.0,
            "moisture_live": 130.0,
            "nh3": "",
            "nox": "",
            "owner": "",
            "pm10": "",
            "pm25": "",
            "rain_days": 8,
            "rot": "",
            "scc": 2810015000,
            "sf_event_guid": "bd1af2ca-a09d-4b1b-9135-ac41132d2e49",
            "sf_server": "playground.dri.edu",
            "sf_stream_name": "realtime",
            "shrub": "",
            "slope": 10.0,
            "snow_month": 5,
            "so2": "",
            "state": "Unknown",
            "sunrise_hour": 6,
            "sunset_hour": 18,
            "type": "RX",
            "veg": "",
            "voc": ""
        }
        expected = {
            "id": "SF11C99165520788816390",
            "event_of":{
                "id": "SF11E589961",
                "url": "http://playground.dri.edu/smartfire/events/bd1af2ca-a09d-4b1b-9135-ac41132d2e49"
            },
            "type": "RX",
            "location":{
                "latitude": 26.286,
                "longitude": -77.118,
                "area": 199.999999503,
                "canopy": "",
                "country": "Unknown",
                "county": "",
                "duff": "",
                "elevation": 0.0,
                "fuel_100hr": "",
                "fuel_10hr": "",
                "fuel_10khr": "",
                "fuel_1hr": "",
                "fuel_1khr": "",
                "fuel_gt10khr": "",
                "grass": "",
                "litter": "",
                "max_humid": 80.0,
                "max_temp": 30.0,
                "max_temp_hour": 14,
                "max_wind": 6.0,
                "max_wind_aloft": 6.0,
                "min_humid": 40.0,
                "min_temp": 13.0,
                "min_temp_hour": 4,
                "min_wind": 6.0,
                "min_wind_aloft": 6.0,
                "moisture_100hr": 12.0,
                "moisture_10hr": 12.0,
                "moisture_1hr": 10.0,
                "moisture_1khr": 22.0,
                "moisture_duff": 150.0,
                "moisture_live": 130.0,
                "rain_days": 8,
                "rot": "",
                "shrub": "",
                "slope": 10.0,
                "snow_month": 5,
                "state": "Unknown",
                "sunrise_hour": 6,
                "sunset_hour": 18
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

    def test_new_sf2_fire(self):
        f = {
            "area": 99.9999997516,
            "canopy": 1.99,
            "ch4": 3.121981000000001,
            "co": 59.839310000000005,
            "co2": 1213.3238309999997,
            "consumption_duff": 0.0,
            "consumption_flaming": 6.95899243316,
            "consumption_residual": 0.0083928461189,
            "consumption_smoldering": 0.462087377634,
            "country": "USA",
            "county": "",
            "date_time": "201508040000-04:00",
            "duff": 0.4,
            "elevation": 0.0,
            "event_id": "SF11E120478",
            "event_url": "http://128.208.123.111/smartfire/events/623343d2-ad25-4532-acd2-4db6cd75068a",
            "fccs_number": 191,
            "fips": 12055,
            "fuel_100hr": 0.4,
            "fuel_10hr": 0.35,
            "fuel_10khr": 0.0,
            "fuel_1hr": 0.08,
            "fuel_1khr": 1.0,
            "fuel_gt10khr": 0.0,
            "grass": 0.16,
            "heat": 1694763710.5973058,
            "id": "SF11C2175237860649980",
            "latitude": 27.303,
            "litter": 0.04,
            "longitude": -81.142,
            "max_humid": 80.0,
            "max_temp": 30.0,
            "max_temp_hour": 14,
            "max_wind": 6.0,
            "max_wind_aloft": 6.0,
            "min_humid": 40.0,
            "min_temp": 13.0,
            "min_temp_hour": 4,
            "min_wind": 6.0,
            "min_wind_aloft": 6.0,
            "moisture_100hr": 12.0,
            "moisture_10hr": 12.0,
            "moisture_1hr": 10.0,
            "moisture_1khr": 22.0,
            "moisture_duff": 150.0,
            "moisture_live": 130.0,
            "nh3": 0.9997780000000001,
            "nox": 1.7264369999999998,
            "owner": "",
            "pm10": 6.900025999999999,
            "pm25": 5.8474879999999985,
            "rain_days": 8,
            "rot": 0.0,
            "scc": 2810015000,
            "sf_event_guid": "623343d2-ad25-4532-acd2-4db6cd75068a",
            "sf_server": "128.208.123.111",
            "sf_stream_name": "realtime",
            "shrub": 4.86,
            "slope": 10.0,
            "snow_month": 5,
            "so2": 0.7279439999999999,
            "state": "FL",
            "sunrise_hour": 6,
            "sunset_hour": 19,
            "timezone": -5.0,
            "type": "RX",
            "veg": "Longleaf pine - Slash pine / Gallberry forest",
            "voc": 14.372022000000001
        }
        expected = {
            "id": "SF11C2175237860649980",
            "type": "RX",
            "event_of": {
                "id": "SF11E120478",
                "url": "http://128.208.123.111/smartfire/events/623343d2-ad25-4532-acd2-4db6cd75068a",
            },
            "location": {
                "latitude": 27.303,
                "longitude": -81.142,
                "area": 99.9999997516,
                "utc_offset": "-04:00",
                "canopy": 1.99,
                "country": "USA",
                "county": "",
                "duff": 0.4,
                "elevation": 0.0,
                "fuel_100hr": 0.4,
                "fuel_10hr": 0.35,
                "fuel_10khr": 0.0,
                "fuel_1hr": 0.08,
                "fuel_1khr": 1.0,
                "fuel_gt10khr": 0.0,
                "grass": 0.16,
                "litter": 0.04,
                "max_humid": 80.0,
                "max_temp": 30.0,
                "max_temp_hour": 14,
                "max_wind": 6.0,
                "max_wind_aloft": 6.0,
                "min_humid": 40.0,
                "min_temp": 13.0,
                "min_temp_hour": 4,
                "min_wind": 6.0,
                "min_wind_aloft": 6.0,
                "moisture_100hr": 12.0,
                "moisture_10hr": 12.0,
                "moisture_1hr": 10.0,
                "moisture_1khr": 22.0,
                "moisture_duff": 150.0,
                "moisture_live": 130.0,
                "rain_days": 8,
                "rot": 0.0,
                "shrub": 4.86,
                "slope": 10.0,
                "snow_month": 5,
                "state": "FL",
                "sunrise_hour": 6,
                "sunset_hour": 19
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
