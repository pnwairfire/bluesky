"""Unit tests for bluesky.fuelmoisture"""

__author__ = "Joel Dubowy"

import datetime

from bluesky.models import fires
from bluesky.fuelmoisture import fill_in_defaults, MOISTURE_PROFILES

class TestFillInDefaults():

    def test_wildfire_no_fm(self):
        f = fires.Fire({
            "type": "wildfire",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2018-11-07T17:00:00",
                            "end": "2018-11-07T19:00:00",
                            "ecoregion": "western",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 500,
                                    "lng": -121.73434,
                                    "lat": 46.7905
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        aa = f['activity'][0]['active_areas'][0]
        loc = f['activity'][0]['active_areas'][0]['specified_points'][0]
        fill_in_defaults(f, aa, loc)

        assert loc['fuelmoisture'] == {
            "2018-11-07T17:00:00": MOISTURE_PROFILES['dry'],
            "2018-11-07T18:00:00": MOISTURE_PROFILES['dry']
        }

    def test_wildfire_no_some_fm_defined(self):
        f = fires.Fire({
            "type": "wildfire",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2018-11-07T17:00:00",
                            "end": "2018-11-07T19:00:00",
                            "ecoregion": "western",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 500,
                                    "lng": -121.73434,
                                    "lat": 46.7905,
                                    "fuelmoisture": {
                                        "2018-11-07T17:00:00": {
                                            "10_hr": 11.234,
                                            "1_hr": 9.865,
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        aa = f['activity'][0]['active_areas'][0]
        loc = f['activity'][0]['active_areas'][0]['specified_points'][0]
        fill_in_defaults(f, aa, loc)

        expected = {
            "2018-11-07T17:00:00": dict(MOISTURE_PROFILES['dry'],
                **{'10_hr': 11.234, '1_hr': 9.865}),
            "2018-11-07T18:00:00": MOISTURE_PROFILES['dry']
        }

        assert loc['fuelmoisture'] == expected

    def test_rx_no_fm(self):
        f = fires.Fire({
            "type": "rx",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2018-11-07T17:00:00",
                            "end": "2018-11-07T19:00:00",
                            "ecoregion": "western",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 500,
                                    "lng": -121.73434,
                                    "lat": 46.7905
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        aa = f['activity'][0]['active_areas'][0]
        loc = f['activity'][0]['active_areas'][0]['specified_points'][0]
        fill_in_defaults(f, aa, loc)

        assert loc['fuelmoisture'] == {
            "2018-11-07T17:00:00": MOISTURE_PROFILES['moist'],
            "2018-11-07T18:00:00": MOISTURE_PROFILES['moist']
        }

    def test_rx_no_some_fm_defined(self):
        f = fires.Fire({
            "type": "rx",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2018-11-07T17:00:00",
                            "end": "2018-11-07T19:00:00",
                            "ecoregion": "western",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 500,
                                    "lng": -121.73434,
                                    "lat": 46.7905,
                                    "fuelmoisture": {
                                        "2018-11-07T17:00:00": {
                                            "10_hr": 20.32,
                                            "1_hr": 21.46,
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        aa = f['activity'][0]['active_areas'][0]
        loc = f['activity'][0]['active_areas'][0]['specified_points'][0]
        fill_in_defaults(f, aa, loc)

        expected = {
            "2018-11-07T17:00:00": dict(MOISTURE_PROFILES['moist'],
                **{'10_hr': 20.32, '1_hr': 21.46}),
            "2018-11-07T18:00:00": MOISTURE_PROFILES['moist']
        }
        assert loc['fuelmoisture'] == expected


    def test_unknown_no_fm(self):
        f = fires.Fire({
            "type": "unknown",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2018-11-07T17:00:00",
                            "end": "2018-11-07T19:00:00",
                            "ecoregion": "western",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 500,
                                    "lng": -121.73434,
                                    "lat": 46.7905
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        aa = f['activity'][0]['active_areas'][0]
        loc = f['activity'][0]['active_areas'][0]['specified_points'][0]
        fill_in_defaults(f, aa, loc)

        assert loc['fuelmoisture'] == {
            "2018-11-07T17:00:00": MOISTURE_PROFILES['moist'],
            "2018-11-07T18:00:00": MOISTURE_PROFILES['moist']
        }

    def test_unknown_no_some_fm_defined(self):
        f = fires.Fire({
            "type": "unknown",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2018-11-07T17:00:00",
                            "end": "2018-11-07T19:00:00",
                            "ecoregion": "western",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 500,
                                    "lng": -121.73434,
                                    "lat": 46.7905,
                                    "fuelmoisture": {
                                        "2018-11-07T17:00:00": {
                                            "10_hr": 19.32,
                                            "1_hr": 43.46,
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        })

        aa = f['activity'][0]['active_areas'][0]
        loc = f['activity'][0]['active_areas'][0]['specified_points'][0]
        fill_in_defaults(f, aa, loc)

        expected = {
            "2018-11-07T17:00:00": dict(MOISTURE_PROFILES['moist'],
                **{'10_hr': 19.32, '1_hr': 43.46}),
            "2018-11-07T18:00:00": MOISTURE_PROFILES['moist']
        }

        assert loc['fuelmoisture'] == expected

