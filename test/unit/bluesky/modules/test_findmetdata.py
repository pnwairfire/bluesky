"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import copy
import datetime
from py.test import raises

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

    def test_no_fires(self):
        fm = FiresManager()
        fm.load({
            "fire_information": []
        })
        with raises(BlueSkyConfigurationError) as e_info:
            findmetdata._get_time_windows(fm)

    def test_fire_no_growth(self):
        fm = FiresManager()
        fm.load({
            "fire_information": [FIRE_NO_GROWTH]
        })
        with raises(BlueSkyConfigurationError) as e_info:
            findmetdata._get_time_windows(fm)

    def test_one_fire(self):
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

    def test_two_fires(self):
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

    def test_three_fires(self):
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


    def test_with_dispersion_window_no_fires(self):
        fm = FiresManager()
        fm.load({
                "config": {
                    "dispersion": {
                        "start": "2014-05-29T19:00:00Z",
                        "num_hours": 12
                    }
                }
            })
        expected = [
            {
                'start': datetime.datetime(2014,5,29,19,0,0),
                'end': datetime.datetime(2014,5,30,7,0,0),
            }
        ]
        assert expected == findmetdata._get_time_windows(fm)

    def test_with_configured_time_window_no_fires(self):
        fm = FiresManager()
        fm.load({
                "config": {
                    "findmetdata": {
                        "time_window": {
                            "first_hour": "2016-01-04T04:00:00Z",
                            "last_hour": "2016-01-05T13:00:00Z"
                        }
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

    def test_with_dispersion_and_configured_time_window_no_fires(self):
        fm = FiresManager()
        fm.load({
                "config": {
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

    def test_with_dispersion_and_configured_time_window_and_three_fires(self):
        fm = FiresManager()
        fm.load({
                "fire_information": [FIRE_1, FIRE_2, FIRE_3],
                "config": {
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


class TestMergeTimeWindows(object):

    def test_simple(self):
        time_windows = [
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)}
        ]
        expected = [
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)}
        ]
        actual = findmetdata._merge_time_windows(time_windows)
        assert actual == expected

    def test_same_start_times_simple(self):
        time_windows = [
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 8, 9, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)}
        ]
        expected = [
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)}
        ]
        actual = findmetdata._merge_time_windows(time_windows)
        assert actual == expected


    def test_same_start_times_real_case_from_sti(self):
        time_windows = [
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 8, 9, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 8, 9, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 8, 9, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 8, 9, 0)},
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 8, 9, 0)},
            {'start': datetime.datetime(2018, 11, 8, 9, 0), 'end': datetime.datetime(2018, 11, 8, 10, 0)},
            {'start': datetime.datetime(2018, 11, 8, 9, 0), 'end': datetime.datetime(2018, 11, 8, 10, 0)},
            {'start': datetime.datetime(2018, 11, 8, 9, 0), 'end': datetime.datetime(2018, 11, 8, 10, 0)},
            {'start': datetime.datetime(2018, 11, 8, 9, 0), 'end': datetime.datetime(2018, 11, 8, 10, 0)},
            {'start': datetime.datetime(2018, 11, 8, 9, 0), 'end': datetime.datetime(2018, 11, 8, 10, 0)},
            {'start': datetime.datetime(2018, 11, 8, 10, 0), 'end': datetime.datetime(2018, 11, 8, 11, 0)},
            {'start': datetime.datetime(2018, 11, 8, 10, 0), 'end': datetime.datetime(2018, 11, 8, 11, 0)},
            {'start': datetime.datetime(2018, 11, 8, 10, 0), 'end': datetime.datetime(2018, 11, 8, 11, 0)},
            {'start': datetime.datetime(2018, 11, 8, 10, 0), 'end': datetime.datetime(2018, 11, 8, 11, 0)},
            {'start': datetime.datetime(2018, 11, 8, 11, 0), 'end': datetime.datetime(2018, 11, 8, 12, 0)},
            {'start': datetime.datetime(2018, 11, 8, 11, 0), 'end': datetime.datetime(2018, 11, 8, 12, 0)},
            {'start': datetime.datetime(2018, 11, 8, 11, 0), 'end': datetime.datetime(2018, 11, 8, 12, 0)},
            {'start': datetime.datetime(2018, 11, 8, 11, 0), 'end': datetime.datetime(2018, 11, 8, 12, 0)},
            {'start': datetime.datetime(2018, 11, 8, 11, 0), 'end': datetime.datetime(2018, 11, 8, 12, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 12, 0), 'end': datetime.datetime(2018, 11, 8, 13, 0)},
            {'start': datetime.datetime(2018, 11, 8, 13, 0), 'end': datetime.datetime(2018, 11, 8, 14, 0)},
            {'start': datetime.datetime(2018, 11, 8, 13, 0), 'end': datetime.datetime(2018, 11, 8, 14, 0)},
            {'start': datetime.datetime(2018, 11, 8, 13, 0), 'end': datetime.datetime(2018, 11, 8, 14, 0)},
            {'start': datetime.datetime(2018, 11, 8, 14, 0), 'end': datetime.datetime(2018, 11, 8, 15, 0)},
            {'start': datetime.datetime(2018, 11, 8, 14, 0), 'end': datetime.datetime(2018, 11, 8, 15, 0)},
            {'start': datetime.datetime(2018, 11, 8, 14, 0), 'end': datetime.datetime(2018, 11, 8, 15, 0)},
            {'start': datetime.datetime(2018, 11, 8, 14, 0), 'end': datetime.datetime(2018, 11, 8, 15, 0)},
            {'start': datetime.datetime(2018, 11, 8, 15, 0), 'end': datetime.datetime(2018, 11, 8, 16, 0)},
            {'start': datetime.datetime(2018, 11, 8, 15, 0), 'end': datetime.datetime(2018, 11, 8, 16, 0)},
            {'start': datetime.datetime(2018, 11, 8, 15, 0), 'end': datetime.datetime(2018, 11, 8, 16, 0)},
            {'start': datetime.datetime(2018, 11, 8, 15, 0), 'end': datetime.datetime(2018, 11, 8, 16, 0)},
            {'start': datetime.datetime(2018, 11, 8, 17, 0), 'end': datetime.datetime(2018, 11, 8, 18, 0)},
            {'start': datetime.datetime(2018, 11, 8, 17, 0), 'end': datetime.datetime(2018, 11, 8, 18, 0)},
            {'start': datetime.datetime(2018, 11, 8, 18, 0), 'end': datetime.datetime(2018, 11, 8, 19, 0)},
            {'start': datetime.datetime(2018, 11, 8, 18, 0), 'end': datetime.datetime(2018, 11, 8, 19, 0)},
            {'start': datetime.datetime(2018, 11, 8, 18, 0), 'end': datetime.datetime(2018, 11, 8, 19, 0)},
            {'start': datetime.datetime(2018, 11, 8, 18, 0), 'end': datetime.datetime(2018, 11, 8, 19, 0)},
            {'start': datetime.datetime(2018, 11, 8, 19, 0), 'end': datetime.datetime(2018, 11, 8, 20, 0)},
            {'start': datetime.datetime(2018, 11, 8, 20, 0), 'end': datetime.datetime(2018, 11, 8, 21, 0)},
            {'start': datetime.datetime(2018, 11, 8, 20, 0), 'end': datetime.datetime(2018, 11, 8, 21, 0)},
            {'start': datetime.datetime(2018, 11, 8, 21, 0), 'end': datetime.datetime(2018, 11, 8, 22, 0)},
            {'start': datetime.datetime(2018, 11, 9, 0, 0), 'end': datetime.datetime(2018, 11, 9, 1, 0)},
            {'start': datetime.datetime(2018, 11, 9, 0, 0), 'end': datetime.datetime(2018, 11, 9, 1, 0)},
            {'start': datetime.datetime(2018, 11, 9, 0, 0), 'end': datetime.datetime(2018, 11, 9, 1, 0)},
            {'start': datetime.datetime(2018, 11, 9, 0, 0), 'end': datetime.datetime(2018, 11, 9, 1, 0)},
            {'start': datetime.datetime(2018, 11, 9, 0, 0), 'end': datetime.datetime(2018, 11, 9, 1, 0)},
            {'start': datetime.datetime(2018, 11, 9, 1, 0), 'end': datetime.datetime(2018, 11, 9, 2, 0)},
            {'start': datetime.datetime(2018, 11, 9, 1, 0), 'end': datetime.datetime(2018, 11, 9, 2, 0)},
            {'start': datetime.datetime(2018, 11, 9, 1, 0), 'end': datetime.datetime(2018, 11, 9, 2, 0)},
            {'start': datetime.datetime(2018, 11, 9, 1, 0), 'end': datetime.datetime(2018, 11, 9, 2, 0)},
            {'start': datetime.datetime(2018, 11, 9, 2, 0), 'end': datetime.datetime(2018, 11, 9, 3, 0)},
            {'start': datetime.datetime(2018, 11, 9, 2, 0), 'end': datetime.datetime(2018, 11, 9, 3, 0)},
            {'start': datetime.datetime(2018, 11, 9, 2, 0), 'end': datetime.datetime(2018, 11, 9, 3, 0)},
            {'start': datetime.datetime(2018, 11, 9, 2, 0), 'end': datetime.datetime(2018, 11, 9, 3, 0)},
            {'start': datetime.datetime(2018, 11, 9, 2, 0), 'end': datetime.datetime(2018, 11, 9, 3, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 3, 0), 'end': datetime.datetime(2018, 11, 9, 4, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 4, 0), 'end': datetime.datetime(2018, 11, 9, 5, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 5, 0), 'end': datetime.datetime(2018, 11, 9, 6, 0)},
            {'start': datetime.datetime(2018, 11, 9, 6, 0), 'end': datetime.datetime(2018, 11, 9, 7, 0)},
            {'start': datetime.datetime(2018, 11, 9, 6, 0), 'end': datetime.datetime(2018, 11, 9, 7, 0)},
            {'start': datetime.datetime(2018, 11, 9, 6, 0), 'end': datetime.datetime(2018, 11, 9, 7, 0)},
            {'start': datetime.datetime(2018, 11, 9, 6, 0), 'end': datetime.datetime(2018, 11, 9, 7, 0)},
            {'start': datetime.datetime(2018, 11, 9, 6, 0), 'end': datetime.datetime(2018, 11, 9, 7, 0)},
            {'start': datetime.datetime(2018, 11, 9, 6, 0), 'end': datetime.datetime(2018, 11, 9, 7, 0)},
            {'start': datetime.datetime(2018, 11, 9, 7, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)},
            {'start': datetime.datetime(2018, 11, 9, 7, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)},
            {'start': datetime.datetime(2018, 11, 9, 7, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)},
            {'start': datetime.datetime(2018, 11, 9, 7, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)},
            {'start': datetime.datetime(2018, 11, 9, 7, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)}
        ]
        expected = [
            {'start': datetime.datetime(2018, 11, 8, 8, 0), 'end': datetime.datetime(2018, 11, 9, 8, 0)}
        ]
        actual = findmetdata._merge_time_windows(time_windows)
        assert actual == expected
