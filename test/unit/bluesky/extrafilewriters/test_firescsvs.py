"""Unit tests for bluesky.extrafilewriters.firescsvs"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.models import fires
from bluesky.extrafilewriters import firescsvs

class TestFiresCsvsPickRepresentativeFuelbed(object):

    def test_invalid_fuelbed(self):
        g = {
            "fuelbeds": 'sdf'
        }
        with raises(TypeError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''

        g = {
            "fuelbeds": [
                {"sdf_fccs_id": "46","pct": 100.0}
            ]
        }
        with raises(KeyError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''
        g = {
            "fuelbeds": [
                {"fccs_id": "46","sdfsdfpct": 100.0}
            ]
        }
        with raises(KeyError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''

    def test_no_fuelbeds(self):
        g = {}
        assert None == firescsvs._pick_representative_fuelbed({}, g)
        g = {
            "activity": []
        }
        assert None == firescsvs._pick_representative_fuelbed({}, g)

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


class TestFiresCsvsWriterCollectCsvFields(object):

    def test(self):
        fire = fires.Fire({
            "fuel_type": "natural",
            "id": "SF11C14225236095807750",
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
                                    "lng": -121.41,
                                    "plumerise": {
                                        "2015-08-04T17:00:00": {
                                            "emission_fractions": [
                                                0.01,0.05,0.05,0.05,0.05,0.05,
                                                0.09,0.09,0.09,0.05,0.05,0.05,
                                                0.05,0.05,0.05,0.05,0.05,0.05,
                                                0.01,0.01
                                            ],
                                            "heights": [
                                                141.438826,
                                                200.84066925000002,
                                                260.2425125,
                                                319.64435575,
                                                379.046199,
                                                438.44804225,
                                                497.84988549999997,
                                                557.25172875,
                                                616.6535719999999,
                                                676.0554152499999,
                                                735.4572585000001,
                                                794.85910175,
                                                854.260945,
                                                913.66278825,
                                                973.0646314999999,
                                                1032.46647475,
                                                1091.868318,
                                                1151.27016125,
                                                1210.6720045,
                                                1270.0738477500001,
                                                1329.475691
                                            ],
                                            "smolder_fraction": 0.05
                                        }
                                    }
                                }
                            ],
                            "state": "WA",
                            "timeprofile": {
                                "2015-08-04T17:00:00": {
                                    "area_fraction": 0.1,
                                    "flaming": 0.2,
                                    "residual": 0.1,
                                    "smoldering": 0.1
                                }
                            }
                        }
                    ],
                }
            ]
        })

        fm = fires.FiresManager()
        fm.add_fire(fire)


        writer = firescsvs.FiresCsvsWriter('/foo')
        fires_fields, events_fields = writer._collect_csv_fields(fm)
        import pdb;pdb.set_trace()

        expected_fires_fields = [{
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
            'heat': 64442794218.7609,
            'id': 'SF11C14225236095807750',
            'latitude': 47.41,
            'longitude': -121.41,
            'max_humid': '',
            'max_temp': '',
            'max_temp_hour': '',
            "min_wind": 34,
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
        }]
        assert fires_fields == expected_fires_fields

        expected_events_fields = [{}]
        assert events_fields == expected_events_fields
