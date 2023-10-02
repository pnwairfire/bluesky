"""Unit tests for bluesky.metutils
"""

__author__ = "Joel Dubowy"

import copy
import datetime

#from pytest import raises

from bluesky import metutils

MET = {
    "files": [
        {
            "first_hour": "2016-09-21T00:00:00",
            "last_hour": "2016-09-21T11:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092100/nam_forecast-2016092100_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-21T12:00:00",
            "last_hour": "2016-09-21T23:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092112/nam_forecast-2016092112_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-22T00:00:00",
            "last_hour": "2016-09-22T11:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092200/nam_forecast-2016092200_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-22T12:00:00",
            "last_hour": "2016-09-22T23:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092212/nam_forecast-2016092212_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-23T00:00:00",
            "last_hour": "2016-09-23T11:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092300/nam_forecast-2016092300_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-23T12:00:00",
            "last_hour": "2016-09-23T23:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092312/nam_forecast-2016092312_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-24T00:00:00",
            "last_hour": "2016-09-24T11:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092400/nam_forecast-2016092400_00-84hr.arl"
        },
        {
            "first_hour": "2016-09-24T12:00:00",
            "last_hour": "2016-09-24T23:00:00",
            "file": "/data/Met/NAM/12km/ARL/2016092412/nam_forecast-2016092412_00-84hr.arl"
        }
    ],
    "grid": {
        "spacing": 6.0,
        "boundary": {
            "ne": {
                "lat": 45.25,
                "lng": -106.5
            },
            "sw": {
                "lat": 27.75,
                "lng": -131.5
            }
        }
    }
}

class TestFilterMet():

    def test_no_filtering_needed(self):
        expected = copy.deepcopy(MET)
        assert expected == metutils.filter_met(MET,
            datetime.datetime(2016,9,21,0,0,0), 100)

    def test_filtering(self):
        expected = copy.deepcopy(MET)

        expected["files"].pop(0)
        assert expected == metutils.filter_met(MET,
            datetime.datetime(2016,9,21,14,0,0), 100)

        expected["files"].pop()
        assert expected == metutils.filter_met(MET,
            datetime.datetime(2016,9,21,14,0,0), 60)
