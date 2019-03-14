"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import copy
import datetime
from py.test import raises

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models.fires import FiresManager
from bluesky.modules import findmetdata


FIRE_NO_GROWTH = {
    "id": "SF11C14225236095807750"
}

FIRE_1 = {
    "growth": [
        {
            "start": "2015-01-20T17:00:00",
            "end": "2015-01-21T17:00:00",
            "location": {
                "latitude": 45,
                "longitude": -119,
                "ecoregion": "southern",
                "utc_offset": "-09:00"
            }
        },
        {
            "pct": 40,
            "start": "2015-01-20T17:00:00", # SAME TIME WINDOW
            "end": "2015-01-21T17:00:00",
            "location": {
                "latitude": 45,
                "longitude": -119,
                "ecoregion": "southern",
                "utc_offset": "-09:00"
            }
        }
    ]
}
FIRE_2 = {
    "growth": [
        {
            "start": "2015-01-21T17:00:00",
            "end": "2015-01-22T17:00:00",
            "location": {
                "latitude": 45,
                "longitude": -119,
                "ecoregion": "southern",
                "utc_offset": "-09:00"
            }
        }
    ]
}
FIRE_3 = {
    "growth": [
        {
            "start": "2015-02-01T17:00:00",
            "end": "2015-02-02T17:00:00",
            "location": {
                "latitude": 45,
                "longitude": -119,
                "ecoregion": "southern",
                "utc_offset": "-07:00"
            }
        }
    ]
}

class TestGetTimeWindows(object):

    def test_no_fires(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fire_information": []
        })
        with raises(BlueSkyConfigurationError) as e_info:
            findmetdata._get_time_windows(fm)

    def test_fire_no_growth(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fire_information": [FIRE_NO_GROWTH]
        })
        with raises(BlueSkyConfigurationError) as e_info:
            findmetdata._get_time_windows(fm)

    def test_one_fire(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fire_information": [FIRE_1]
        })
        expected = [
            {
                'start': datetime.datetime(2015,1,21,2,0,0),
                'end': datetime.datetime(2015,1,22,2,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)

    def test_two_fires(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fire_information": [FIRE_1, FIRE_2]
        })
        expected = [
            {
                'start': datetime.datetime(2015,1,21,2,0,0),
                'end': datetime.datetime(2015,1,23,2,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)

    def test_three_fires(self, reset_config):
        fm = FiresManager()
        fm.load({
            "fire_information": [FIRE_1, FIRE_2, FIRE_3]
        })
        expected = [
            {
                'start': datetime.datetime(2015,1,21,2,0,0),
                'end': datetime.datetime(2015,1,23,2,0,0),
            },
            {
                'start': datetime.datetime(2015,2,2,0,0,0),
                'end': datetime.datetime(2015,2,3,0,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)


    def test_with_dispersion_window_no_fires(self, reset_config):
        fm = FiresManager()
        Config.set({
            "dispersion": {
                "start": "2014-05-29T19:00:00Z",
                "num_hours": 12
            }
        })
        expected = [
            {
                'start': datetime.datetime(2014,5,29,19,0,0),
                'end': datetime.datetime(2014,5,30,7,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)

    def test_with_configured_time_window_no_fires(self, reset_config):
        fm = FiresManager()
        Config.set({
            "findmetdata": {
                "time_window": {
                    "first_hour": "2016-01-04T04:00:00Z",
                    "last_hour": "2016-01-05T13:00:00Z"
                }
            }
        })
        expected = [
            {
                'start': datetime.datetime(2016,1,4,4,0,0),
                'end': datetime.datetime(2016,1,5,13,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)

    def test_with_dispersion_and_configured_time_window_no_fires(self, reset_config):
        fm = FiresManager()
        Config.set({
            "dispersion": {
                "start": "2014-05-29T19:00:00Z",
                "num_hours": 12
            },
            "findmetdata": {
                "time_window": {
                    "first_hour": "2016-01-04T04:00:00Z",
                    "last_hour": "2016-01-05T13:00:00Z"
                }
            }
        })

        expected = [
            {
                'start': datetime.datetime(2014,5,29,19,0,0),
                'end': datetime.datetime(2014,5,30,7,0,0),
            },
            {
                'start': datetime.datetime(2016,1,4,4,0,0),
                'end': datetime.datetime(2016,1,5,13,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)

    def test_with_dispersion_and_configured_time_window_and_three_fires(self, reset_config):
        fm = FiresManager()
        fm.load({
                "fire_information": [FIRE_1, FIRE_2, FIRE_3],
        })
        Config.set( {
            "dispersion": {
                "start": "2014-05-29T19:00:00Z",
                "num_hours": 12
            },
            "findmetdata": {
                "time_window": {
                    "first_hour": "2016-01-04T04:00:00Z",
                    "last_hour": "2016-01-05T13:00:00Z"
                }
            }
        })
        expected = [
            {
                'start': datetime.datetime(2014,5,29,19,0,0),
                'end': datetime.datetime(2014,5,30,7,0,0),
            },
            {
                'start': datetime.datetime(2015,1,21,2,0,0),
                'end': datetime.datetime(2015,1,23,2,0,0),
            },
            {
                'start': datetime.datetime(2015,2,2,0,0,0),
                'end': datetime.datetime(2015,2,3,0,0,0),
            },
            {
                'start': datetime.datetime(2016,1,4,4,0,0),
                'end': datetime.datetime(2016,1,5,13,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)
