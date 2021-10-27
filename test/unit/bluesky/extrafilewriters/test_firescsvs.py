"""Unit tests for bluesky.extrafilewriters.firescsvs"""

__author__ = "Joel Dubowy"

import copy

from py.test import raises

from bluesky.config import Config
from bluesky.models.fires import Fire
from bluesky.extrafilewriters import firescsvs

class TestFiresCsvsPickRepresentativeFuelbed(object):

    def test_invalid_fuelbed(self):
        g = {
            "fuelbeds": 'sdf'
        }
        with raises(AttributeError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''

    def test_no_fuelbeds(self):
        g = {}
        assert None == firescsvs._pick_representative_fuelbed({}, g)
        g = {
            "activity": []
        }
        assert None == firescsvs._pick_representative_fuelbed({}, g)

    def test_one_fuelbed_no_fccs_id(self):
        g = {
            "fuelbeds": [
                {"pct": 100.0}
            ]
        }
        assert None == firescsvs._pick_representative_fuelbed({}, g)

        g["fuelbeds"][0]["sdf_fccs_id"] = "46"
        assert None == firescsvs._pick_representative_fuelbed({}, g)

    def test_one_fuelbed_no_pct(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46"}
            ]
        }
        assert "46" == firescsvs._pick_representative_fuelbed({}, g)

    def test_two_fuelbeds_one_with_no_pct(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46"},
                {"fccs_id": "44","pct": 100.0}
            ]
        }
        assert "44" == firescsvs._pick_representative_fuelbed({}, g)


    def test_one_fuelbed(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0}
            ]
        }
        assert "46" == firescsvs._pick_representative_fuelbed({}, g)

    def test_three_fuelbed(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 10.0},
                {"fccs_id": "47","pct": 60.0},
                {"fccs_id": "48","pct": 30.0}
            ]
        }
        assert "47" == firescsvs._pick_representative_fuelbed({}, g)

    def test_two_equal_size_fuelbeds(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0},
                {"fccs_id": "44","pct": 100.0}
            ]
        }
        assert "46" == firescsvs._pick_representative_fuelbed({}, g)


class TestFiresCsvsFormatDatetime(object):

    FIRE = Fire({
        "activity": [
            {
                "active_areas": [
                    {
                        "start": "2015-08-04T18:00:00",
                        "end": "2015-08-05T18:00:00",
                        "utc_offset": "-06:00",
                        "specified_points": [
                            {
                                "lat": 35.0,
                                "lng": -96.2,
                                "area": 99
                            }
                        ]
                    }
                ]
            }
        ]
    })
    LOC = FIRE['activity'][0]['active_areas'][0]['specified_points'][0]
    FIRE_NO_OFFSET = copy.deepcopy(FIRE)
    FIRE_NO_OFFSET['activity'][0]['active_areas'][0].pop('utc_offset')
    LOC_NO_OFFSET = FIRE_NO_OFFSET['activity'][0]['active_areas'][0]['specified_points'][0]

    def teardown(self):
        # TODO: figure out why this is required, even with
        #    'reset_config' in each test method's signature
        Config().reset()

    def test_default_date_time(self):
        s = firescsvs._format_date_time(self.FIRE, self.LOC)
        assert s == '20150804'

    def test_custom_date_time(self, reset_config):
        Config().set("%Y%m%d%H%M%z", 'extrafiles', 'firescsvs',
            'date_time_format')
        s = firescsvs._format_date_time(self.FIRE, self.LOC)
        assert s == '201508041800-0600'

    def test_custom_date_time_missing_offset(self, reset_config):
        Config().set("%Y%m%d%H%M%z", 'extrafiles', 'firescsvs',
            'date_time_format')
        s = firescsvs._format_date_time(self.FIRE_NO_OFFSET, self.LOC_NO_OFFSET)
        assert s == '201508041800'

    def test_bsf_date_time(self, reset_config):
        Config().set("%Y%m%d0000%z", 'extrafiles', 'firescsvs',
            'date_time_format')
        s = firescsvs._format_date_time(self.FIRE, self.LOC)
        assert s == '201508040000-0600'


class TestFiresCsvsWriterCollectCsvFields(object):

    def test_one_fire_no_event(self):
        fire = Fire({
            "fuel_type": "natural",
            "id": "SF11C14225236095807750",
            "type": "wildfire",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2015-08-04T18:00:00",
                            "end": "2015-08-05T18:00:00",
                            "utc_offset": "-06:00",
                            "specified_points": [
                                {
                                    "lat": 35.0,
                                    "lng": -96.2,
                                    "area": 99,
                                    "source": "GOES-16"
                                }
                            ]
                        },
                        {
                            "start": "2015-08-04T17:00:00",
                            "end": "2015-08-05T17:00:00",
                            "utc_offset": "-07:00",
                            "canopy_consumption_pct": 23.3,
                            "min_wind": 34,
                            "specified_points": [
                                {
                                    "lat": 30.0,
                                    "lng": -116.2,
                                    "area": 102
                                },
                                {
                                    "area": 120.0,
                                    "rain_days": 8,
                                    "slope": 20.0,
                                    "snow_month": 5,
                                    "sunrise_hour": 4,
                                    "sunset_hour": 19,
                                    "consumption": {
                                        "summary": {
                                            "flaming": 1311.2071801109494,
                                            "residual": 1449.3962581338644,
                                            "smoldering": 1267.0712004277434,
                                            "total": 4027.6746386725567
                                        }
                                    },
                                    "fuelbeds": [
                                        {
                                            "emissions": {
                                                "flaming": {
                                                    "PM2.5": [9.545588271207714]
                                                },
                                                "residual": {
                                                    "PM2.5": [24.10635856528243]
                                                },
                                                "smoldering": {
                                                    "PM2.5": [21.073928205514225]
                                                },
                                                "total": {
                                                    "PM2.5": [54.725875042004375]
                                                }
                                            },
                                            "fccs_id": "9",
                                            "heat": {
                                                "flaming": [20979314881.77519],
                                                "residual": [23190340130.141827],
                                                "smoldering": [20273139206.843895],
                                                "total": [64442794218.7609]
                                            },
                                            "pct": 100.0
                                        }
                                    ],
                                    "lat": 47.41,
                                    "lng": -121.41
                                }
                            ],
                            "state": "WA"
                        }
                    ],
                }
            ]
        })

        writer = firescsvs.FiresCsvsWriter('/foo')
        fires_fields, events_fields = writer._collect_csv_fields([fire])

        expected_fires_fields = [
            {
                "source": "GOES-16",
                "area": 99,
                "canopy_consumption_pct": '',
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': '',
                'event_name': '',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 35.0,
                "longitude": -96.2,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': '',
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': '',
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': '',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-06:00",
                'voc': ''
            },
            {
                "source": "",
                "area": 102,
                "canopy_consumption_pct": 23.3,
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': '',
                'event_name': '',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 30.0,
                "longitude": -116.2,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                "min_wind": 34,
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': '',
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': 'WA',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-07:00",
                'voc': ''
            },
            {
                'source': "",
                'area': 120.0,
                "canopy_consumption_pct": 23.3,
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': 1311.2071801109494,
                'consumption_residual': 1449.3962581338644,
                'consumption_smoldering': 1267.0712004277434,
                'consumption_total': 4027.6746386725567,
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': '',
                'event_name': '',
                'fccs_number': '9',
                'fuelbed_fractions': '9 1.0',
                'heat': 64442794218.7609,
                'id': 'SF11C14225236095807750',
                'latitude': 47.41,
                'longitude': -121.41,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': 34,
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 54.725875042004375,
                'rain_days': 8.0,
                'slope': 20.0,
                'snow_month': 5.0,
                'so2': '',
                'state': 'WA',
                'sunrise_hour': 4.0,
                'sunset_hour': 19.0,
                'type': 'WF',
                'utc_offset': '-07:00',
                'voc': ''
            }
        ]

        assert len(fires_fields) == len(expected_fires_fields)
        for i in range(len(fires_fields)):
            assert fires_fields[i].keys() == expected_fires_fields[i].keys()
            for k in fires_fields[i]:
                assert fires_fields[i][k] == expected_fires_fields[i][k], "{} differs".format(k)

        expected_events_fields = {}
        assert events_fields == expected_events_fields


    def test_two_fires_one_event(self):
        fires = [
            Fire({
                "fuel_type": "natural",
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "bigeventid"
                    # purposely missing 'name'
                },
                "type": "wildfire",
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2015-08-04T18:00:00",
                                "end": "2015-08-05T18:00:00",
                                "utc_offset": "-06:00",
                                "specified_points": [
                                    {
                                        "lat": 35.0,
                                        "lng": -96.2,
                                        "area": 99,
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "total": {
                                                        "PM2.5": [10]
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            },
                        ]
                    }
                ]
            }),
            Fire({
                "fuel_type": "natural",
                "id": "SF11C14225236095807750-B",
                "event_of": {
                    "id": "bigeventid",
                    "name": "big event name"
                },
                "type": "wildfire",
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2015-08-04T17:00:00",
                                "end": "2015-08-05T17:00:00",
                                "utc_offset": "-07:00",
                                "canopy_consumption_pct": 23.3,
                                "min_wind": 34,
                                "specified_points": [
                                    {
                                        "lat": 30.0,
                                        "lng": -116.2,
                                        "area": 102
                                    },
                                    {
                                        "area": 120.0,
                                        "rain_days": 8,
                                        "slope": 20.0,
                                        "snow_month": 5,
                                        "sunrise_hour": 4,
                                        "sunset_hour": 19,
                                        "consumption": {
                                            "summary": {
                                                "flaming": 1311.2071801109494,
                                                "residual": 1449.3962581338644,
                                                "smoldering": 1267.0712004277434,
                                                "total": 4027.6746386725567
                                            }
                                        },
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "flaming": {
                                                        "PM2.5": [9.545588271207714]
                                                    },
                                                    "residual": {
                                                        "PM2.5": [24.10635856528243]
                                                    },
                                                    "smoldering": {
                                                        "PM2.5": [21.073928205514225]
                                                    },
                                                    "total": {
                                                        "PM2.5": [54.725875042004375]
                                                    }
                                                },
                                                "fccs_id": "9",
                                                "heat": {
                                                    "flaming": [20979314881.77519],
                                                    "residual": [23190340130.141827],
                                                    "smoldering": [20273139206.843895],
                                                    "total": [64442794218.7609]
                                                },
                                                "pct": 100.0
                                            }
                                        ],
                                        "lat": 47.41,
                                        "lng": -121.41
                                    },
                                    {
                                        "area": 120.0,
                                        "rain_days": 8,
                                        "slope": 20.0,
                                        "snow_month": 5,
                                        "sunrise_hour": 4,
                                        "sunset_hour": 19,
                                        "consumption": {
                                            "summary": {
                                                "flaming": 1311.2071801109494,
                                                "residual": 1449.3962581338644,
                                                "smoldering": 1267.0712004277434,
                                                "total": 4027.6746386725567
                                            }
                                        },
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "flaming": {
                                                        "PM2.5": [9.545588271207714]
                                                    },
                                                    "residual": {
                                                        "PM2.5": [24.10635856528243]
                                                    },
                                                    "smoldering": {
                                                        "PM2.5": [21.073928205514225]
                                                    },
                                                    "total": {
                                                        "PM2.5": [54.725875042004375]
                                                    }
                                                },
                                                "fccs_id": "9",
                                                "heat": {
                                                    "flaming": [20979314881.77519],
                                                    "residual": [23190340130.141827],
                                                    "smoldering": [20273139206.843895],
                                                    "total": [64442794218.7609]
                                                },
                                                "pct": 40.0
                                            },
                                            {
                                                "emissions": {
                                                    "flaming": {
                                                        "PM2.5": [0]
                                                    },
                                                    "residual": {
                                                        "PM2.5": [0]
                                                    },
                                                    "smoldering": {
                                                        "PM2.5": [0]
                                                    },
                                                    "total": {
                                                        "PM2.5": [10]
                                                    }
                                                },
                                                "fccs_id": "52",
                                                "heat": {
                                                    "flaming": [0],
                                                    "residual": [0],
                                                    "smoldering": [0],
                                                    "total": [0]
                                                },
                                                "pct": 60.0
                                            }
                                        ],
                                        "lat": 47.41,
                                        "lng": -121.41
                                    }
                                ],
                                "state": "WA"
                            }
                        ],
                    }
                ]
            })
        ]


        writer = firescsvs.FiresCsvsWriter('/foo')
        fires_fields, events_fields = writer._collect_csv_fields(fires)

        expected_fires_fields = [
            {
                "source": "",
                "area": 99,
                "canopy_consumption_pct": '',
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': '',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 35.0,
                "longitude": -96.2,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': '',
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 10.0,
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': '',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-06:00",
                'voc': ''
            },
            {
                "source": "",
                "area": 102,
                "canopy_consumption_pct": 23.3,
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': 'big event name',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750-B',
                "latitude": 30.0,
                "longitude": -116.2,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                "min_wind": 34,
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': '',
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': 'WA',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-07:00",
                'voc': ''
            },
            {
                'source': "",
                'area': 120.0,
                "canopy_consumption_pct": 23.3,
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': 1311.2071801109494,
                'consumption_residual': 1449.3962581338644,
                'consumption_smoldering': 1267.0712004277434,
                'consumption_total': 4027.6746386725567,
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': 'big event name',
                'fccs_number': '9',
                'fuelbed_fractions': '9 1.0',
                'heat': 64442794218.7609,
                'id': 'SF11C14225236095807750-B',
                'latitude': 47.41,
                'longitude': -121.41,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': 34,
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 54.725875042004375,
                'rain_days': 8.0,
                'slope': 20.0,
                'snow_month': 5.0,
                'so2': '',
                'state': 'WA',
                'sunrise_hour': 4.0,
                'sunset_hour': 19.0,
                'type': 'WF',
                'utc_offset': '-07:00',
                'voc': ''
            },
            {
                'source': "",
                'area': 120.0,
                "canopy_consumption_pct": 23.3,
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': 1311.2071801109494,
                'consumption_residual': 1449.3962581338644,
                'consumption_smoldering': 1267.0712004277434,
                'consumption_total': 4027.6746386725567,
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': 'big event name',
                'fccs_number': '52',
                'fuelbed_fractions': '52 0.6; 9 0.4',
                'heat': 64442794218.7609,
                'id': 'SF11C14225236095807750-B',
                'latitude': 47.41,
                'longitude': -121.41,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': 34,
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 64.725875042004375,
                'rain_days': 8.0,
                'slope': 20.0,
                'snow_month': 5.0,
                'so2': '',
                'state': 'WA',
                'sunrise_hour': 4.0,
                'sunset_hour': 19.0,
                'type': 'WF',
                'utc_offset': '-07:00',
                'voc': ''
            }
        ]

        assert len(fires_fields) == len(expected_fires_fields)
        for i in range(len(fires_fields)):
            assert fires_fields[i].keys() == expected_fires_fields[i].keys()
            for k in fires_fields[i]:
                assert fires_fields[i][k] == expected_fires_fields[i][k], "{} differs".format(k)

        expected_events_fields = {
            'bigeventid': {
                'name':'big event name',
                'total_area': 441.0,
                'total_ch4': None,
                'total_co': None,
                'total_co2': None,
                'total_heat': None,
                'total_nh3': None,
                'total_nmhc': None,
                'total_nox': None,
                'total_pm10': None,
                'total_pm2.5': None, # because pm2.5 wasn't defined for one location
                'total_so2': None,
                'total_voc': None
            }
        }
        assert events_fields == expected_events_fields

    def test_two_fires_one_event_two_days(self):
        fires = [
            Fire({
                "fuel_type": "natural",
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "bigeventid"
                    # purposely missing 'name'
                },
                "type": "wildfire",
                # two days defined as two active areas in the same
                # actividy object
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2015-08-04T18:00:00",
                                "end": "2015-08-05T18:00:00",
                                "utc_offset": "-06:00",
                                "specified_points": [
                                    {
                                        "lat": 35.0,
                                        "lng": -96.2,
                                        "area": 99,
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "total": {
                                                        "PM2.5": [10]
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "start": "2015-08-05T18:00:00",
                                "end": "2015-08-06T18:00:00",
                                "utc_offset": "-06:00",
                                "specified_points": [
                                    {
                                        "lat": 35.0,
                                        "lng": -96.2,
                                        "area": 99,
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "total": {
                                                        "PM2.5": [20]
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            },
                        ]
                    }
                ]
            }),
            Fire({
                "fuel_type": "natural",
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "bigeventid",
                    "name": "foo-event"
                },
                "type": "wildfire",
                # two days defined as two activity objects, each with
                # one active area
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2015-08-04T18:00:00",
                                "end": "2015-08-05T18:00:00",
                                "utc_offset": "-06:00",
                                "specified_points": [
                                    {
                                        "lat": 35.5,
                                        "lng": -96.0,
                                        "area": 200,
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "total": {
                                                        "PM2.5": [30]
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "active_areas": [
                            {
                                "start": "2015-08-05T18:00:00",
                                "end": "2015-08-06T18:00:00",
                                "utc_offset": "-06:00",
                                "specified_points": [
                                    {
                                        "lat": 35.5,
                                        "lng": -96.0,
                                        "area": 200,
                                        "fuelbeds": [
                                            {
                                                "emissions": {
                                                    "total": {
                                                        "PM2.5": [40]
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            },
                        ]
                    }
                ]
            })
        ]


        writer = firescsvs.FiresCsvsWriter('/foo')
        fires_fields, events_fields = writer._collect_csv_fields(fires)

        expected_fires_fields = [
            {
                "source": "",
                "area": 99,
                "canopy_consumption_pct": '',
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': '',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 35.0,
                "longitude": -96.2,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': '',
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 10.0,
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': '',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-06:00",
                'voc': ''
            },
            {
                "source": "",
                "area": 99,
                "canopy_consumption_pct": '',
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150805',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': '',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 35.0,
                "longitude": -96.2,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': '',
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 20.0,
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': '',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-06:00",
                'voc': ''
            },
            {
                "source": "",
                "area": 200,
                "canopy_consumption_pct": '',
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150804',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': 'foo-event',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 35.5,
                "longitude": -96.0,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': '',
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 30.0,
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': '',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-06:00",
                'voc': ''
            },
            {
                "source": "",
                "area": 200,
                "canopy_consumption_pct": '',
                'ch4': '',
                'co': '',
                'co2': '',
                'consumption_flaming': '',
                'consumption_residual': '',
                'consumption_smoldering': '',
                'consumption_total': '',
                'country': '',
                'county': '',
                'date_time': '20150805',
                'elevation': '',
                'event_id': 'bigeventid',
                'event_name': 'foo-event',
                'fccs_number': '',
                'fuelbed_fractions': '',
                'heat': '',
                'id': 'SF11C14225236095807750',
                "latitude": 35.5,
                "longitude": -96.0,
                'max_humid': '',
                'max_temp': '',
                'max_temp_hour': '',
                'max_wind': '',
                'max_wind_aloft': '',
                'min_humid': '',
                'min_temp': '',
                'min_temp_hour': '',
                'min_wind': '',
                'min_wind_aloft': '',
                'moisture_100hr': '',
                'moisture_10hr': '',
                'moisture_1hr': '',
                'moisture_1khr': '',
                'moisture_duff': '',
                'moisture_live': '',
                'nh3': '',
                'nox': '',
                'pm10': '',
                'pm2.5': 40.0,
                'rain_days': '',
                'slope': '',
                'snow_month': '',
                'so2': '',
                'state': '',
                'sunrise_hour': '',
                'sunset_hour': '',
                'type': 'WF',
                "utc_offset": "-06:00",
                'voc': ''
            }
        ]

        assert len(fires_fields) == len(expected_fires_fields)
        for i in range(len(fires_fields)):
            assert fires_fields[i].keys() == expected_fires_fields[i].keys()
            for k in fires_fields[i]:
                assert fires_fields[i][k] == expected_fires_fields[i][k], "{} differs".format(k)

        expected_events_fields = {
            'bigeventid': {
                'name':'foo-event',
                'total_area': 598,
                'total_ch4': None,
                'total_co': None,
                'total_co2': None,
                'total_heat': None,
                'total_nh3': None,
                'total_nmhc': None,
                'total_nox': None,
                'total_pm10': None,
                'total_pm2.5': 100, # because pm2.5 wasn't defined for one location
                'total_so2': None,
                'total_voc': None
            }
        }
        assert events_fields == expected_events_fields
