"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import datetime

from py.test import raises
from plumerise import sev, feps

from bluesky.config import Config, defaults
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models.fires import FiresManager, Fire
from bluesky.models import activity
from bluesky.modules import plumerising


FIRE_NO_ACTIVITY = Fire({
    "id": "SF11C14225236095807750"
})

FIRE_MISSING_LOCATION_AREA = Fire({
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
                        "lng": -119
                    }]
                }
            ]
        }
    ]
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
                        "area": 3232,
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



_PR_ARGS = None
_PR_KWARGS = None
_PR_COMPUTE_CALL_ARGS = None
_PR_COMPUTE_CALL_KWARGS = None

class MockPlumeRise(object):
    def __init__(self, *args, **kwargs):
        global _PR_ARGS, _PR_KWARGS, _PR_COMPUTE_CALL_ARGS
        _PR_ARGS = args
        _PR_KWARGS = kwargs
        _PR_COMPUTE_CALL_ARGS = []
        _PR_COMPUTE_CALL_KWARGS = {}

    def compute(self, *args, **kwargs):
        _PR_COMPUTE_CALL_ARGS.append(args)
        _PR_COMPUTE_CALL_KWARGS.append(args)
        return "compute return value"

def monkeypatch_plumerise_class(monkeypatch):
    monkeypatch.setattr(sev, 'SEVPlumeRise', MockPlumeRise)
    monkeypatch.setattr(feps, 'FEPSPlumeRise', MockPlumeRise)

# TODO: mock pyairfire.sun.Sun

class TestPlumeRiseRun(object):

    def test_invalid_module(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)
        Config.set('sdf', 'plumerising', 'model')
        fm = FiresManager()
        with raises(BlueSkyConfigurationError) as e_info:
            plumerising.run(fm)
        assert e_info.value.args[0] == plumerising.INVALID_PLUMERISE_MODEL_MSG.format('sdf')

class TestPlumeRiseRunFeps(object):

    def setup(self):
        Config.set('feps', 'plumerising', 'model')
        self.fm = FiresManager()

    def test_fire_no_activity(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_NO_ACTIVITY]})
        with raises(ValueError) as e_info:
            plumerising.run(self.fm)
        assert e_info.value.args[0] == plumerising.NO_ACTIVITY_ERROR_MSG

    def test_fire_missing_location_area(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_LOCATION_AREA]})
        with raises(ValueError) as e_info:
            plumerising.run(self.fm)
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']

    def test_no_fires(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": []})
        plumerising.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerising']['feps']
        assert _PR_COMPUTE_CALL_ARGS == []

    def test_one_fire(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE]})
        plumerising.run(self.fm)

        assert _PR_ARGS == (None, )
        assert _PR_KWARGS == {}
        assert _PR_COMPUTE_CALL_ARGS == [
            (45.0, -119.0, datetime.datetime(2015, 1, 20, 17, 0), datetime.datetime(2015, 1, 21, 17, 0), -7.0),
            (47.418, -121.426, datetime.datetime(2015, 1, 21, 17, 0), datetime.datetime(2015, 1, 22, 17, 0), -7.0)
        ]


class TestPlumeRiseRunSev(object):

    def setup(self):
        Config.set('sev', 'plumerising', 'model')
        self.fm = FiresManager()
