"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import datetime

from py.test import raises
from met.arl import arlprofiler

from bluesky.config import defaults, Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models.fires import FiresManager, Fire
from bluesky.modules import localmet



FIRE_NO_ACTIVITY = Fire({
    "id": "SF11C14225236095807750"
})

FIRE = Fire({
    "activity": [
        {
            "active_areas": [
                {
                    "start": "2015-01-20T17:00:00",
                    "end": "2015-01-21T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "specified_points": [{
                        "lat": 45,
                        "lng": -119,
                        "area": 123
                    }]
                },
                {
                    "pct": 40,
                    "start": "2015-01-21T17:00:00", # SAME TIME WINDOW
                    "end": "2015-01-22T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "perimeter": {
                        "polygon": [
                            [-121.45, 47.43],
                            [-121.39, 47.43],
                            [-121.39, 47.40],
                            [-121.45, 47.40],
                            [-121.45, 47.43]
                        ]
                    }
                }
            ]
        }
    ]
})
MET_INFO = {
   "files": [
       {
           "file": "/DRI_6km/2014052912/wrfout_d2.2014052912.f00-11_12hr01.arl",
           "first_hour": "2015-01-20T12:00:00",
           "last_hour": "2015-01-20T23:00:00"
       },
       {
           "file": "/DRI_6km/2014053000/wrfout_d2.2014053000.f00-11_12hr01.arl",
           "first_hour": "2015-01-22T00:00:00",
           "last_hour": "2015-01-22T11:00:00"
       }
   ],
}



_ARLP_ARGS = None
_ARLP_KWARGS = None
_ARLP_PROFILE_CALL_ARGS = None

class MockArlProfiler(object):
    def __init__(self, *args, **kwargs):
        global _ARLP_ARGS, _ARLP_KWARGS, _ARLP_PROFILE_CALL_ARGS
        _ARLP_ARGS = args
        _ARLP_KWARGS = kwargs
        _ARLP_PROFILE_CALL_ARGS = []

    def profile(self, *args):
        _ARLP_PROFILE_CALL_ARGS.append(args)
        return [{}] * len(args[2])

def monkeypatch_arl_profiler(monkeypatch):
    monkeypatch.setattr(arlprofiler, 'ArlProfiler', MockArlProfiler)

class TestLocalMetRun(object):

    def test_no_met(self, reset_config, monkeypatch):
        monkeypatch_arl_profiler(monkeypatch)

        fm = FiresManager()
        fm.load({
            "fires": [FIRE]
        })
        with raises(ValueError) as e_info:
            localmet.run(fm)
        assert e_info.value.args[0] == localmet.NO_MET_ERROR_MSG

    def test_fire_no_activity(self, reset_config, monkeypatch):
        Config().set(False, 'skip_failed_fires')
        monkeypatch_arl_profiler(monkeypatch)

        fm = FiresManager()
        fm.met = MET_INFO
        fm.load({
            "fires": [FIRE_NO_ACTIVITY]
        })
        with raises(ValueError) as e_info:
            localmet.run(fm)
        assert e_info.value.args[0] == localmet.NO_ACTIVITY_ERROR_MSG

    def test_no_fires(self, reset_config, monkeypatch):
        monkeypatch_arl_profiler(monkeypatch)

        fm = FiresManager()
        fm.met = MET_INFO
        fm.load({
            "fires": []
        })
        with raises(RuntimeError) as e_info:
            localmet.run(fm)
        assert e_info.value.args[0] == localmet.NO_START_OR_END_ERROR_MSG

    def test_one_fire(self, reset_config, monkeypatch):
        monkeypatch_arl_profiler(monkeypatch)

        fm = FiresManager()
        fm.met = MET_INFO
        fm.load({
            "fires": [FIRE]
        })
        localmet.run(fm)

        assert _ARLP_ARGS == (MET_INFO['files'], )
        assert _ARLP_KWARGS == {'time_step': defaults._DEFAULTS['localmet']['time_step']}
        assert _ARLP_PROFILE_CALL_ARGS == [
            (
                datetime.datetime(2015, 1, 21, 0, 0),
                datetime.datetime(2015, 1, 22, 0, 0),
                [
                    {'latitude': 45.0, 'longitude': -119.0},
                    {'latitude': 47.415, 'longitude': -121.42}
                ]
            )
        ]
