"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import datetime

from py.test import raises
from plumerise import sev, feps

from bluesky.config import Config, defaults
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models.fires import FiresManager, Fire
from bluesky.models import activity
from bluesky.modules import plumerise


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

FIRE_MISSING_CONSUMPTION = Fire({
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
                    }],
                    "timeprofile": {"foo": 1},
                    "localmet": {"baz": 444}
                }
            ]
        }
    ]
})

FIRE_MISSING_TIMEPROFILE = Fire({
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
                        "area": 123,
                        "consumption": {"summary":{"smoldering": 123}}
                    }],
                    "localmet": {"baz": 444}
                }
            ]
        }
    ]
})

FIRE_MISSING_START_TIME = Fire({
    "activity": [
        {
            "active_areas": [
                {
                    "end": "2015-01-21T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "specified_points": [{
                        "lat": 45,
                        "lng": -119,
                        "area": 123,
                        "consumption": {"summary":{"smoldering": 123}}
                    }],
                    "timeprofile": {"foo": 1},
                    "localmet": {"baz": 444}
                }
            ]
        }
    ]
})


FIRE_MISSING_LOCALMET = Fire({
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
                        "area": 123,
                        "consumption": {"summary":{"smoldering": 123}}
                    }],
                    "timeprofile": {"foo": 1}
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
                        "area": 123,
                        "consumption": {"summary":{"smoldering": 123}}
                    }],
                    "timeprofile": {"foo": 1},
                    "localmet": {"baz": 444}
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
                        ],
                        "consumption": {"summary":{"flaming": 434}}
                    },
                    "timeprofile": {"bar": 2},
                    "localmet": {"bazoo": 555}
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
        global _PR_ARGS, _PR_KWARGS, _PR_COMPUTE_CALL_ARGS, _PR_COMPUTE_CALL_KWARGS
        _PR_ARGS = args
        _PR_KWARGS = kwargs
        _PR_COMPUTE_CALL_ARGS = []
        _PR_COMPUTE_CALL_KWARGS = []

    def compute(self, *args, **kwargs):
        _PR_COMPUTE_CALL_ARGS.append(args)
        _PR_COMPUTE_CALL_KWARGS.append(kwargs)
        return {"hours": "compute return value"}

def monkeypatch_plumerise_class(monkeypatch):
    monkeypatch.setattr(sev, 'SEVPlumeRise', MockPlumeRise)
    monkeypatch.setattr(feps, 'FEPSPlumeRise', MockPlumeRise)

# TODO: mock pyairfire.sun.Sun

class TestPlumeRiseRun(object):

    def test_invalid_module(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)
        Config().set('sdf', 'plumerise', 'model')
        fm = FiresManager()
        with raises(BlueSkyConfigurationError) as e_info:
            plumerise.run(fm)
        assert e_info.value.args[0] == plumerise.INVALID_PLUMERISE_MODEL_MSG.format('sdf')

class TestPlumeRiseRunFeps(object):

    def setup(self):
        Config().set('feps', 'plumerise', 'model')
        self.fm = FiresManager()

    def test_fire_no_activity(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_NO_ACTIVITY]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == plumerise.NO_ACTIVITY_ERROR_MSG

    def test_fire_missing_location_area(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_LOCATION_AREA]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']

    def test_fire_missing_location_consumption(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_CONSUMPTION]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == plumerise.MISSING_CONSUMPTION_ERROR_MSG

    def test_fire_missing_timeprofile(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_TIMEPROFILE]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == plumerise.MISSING_TIMEPROFILE_ERROR_MSG

    def test_fire_missing_start_time(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_START_TIME]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == plumerise.MISSING_START_TIME_ERROR_MSG

    # TODO: test with invalid start time


    def test_fire_missing_localmet(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_LOCALMET]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        loc1 = FIRE_MISSING_LOCALMET['activity'][0]['active_areas'][0]['specified_points'][0]
        assert _PR_COMPUTE_CALL_ARGS == [
            ({"foo": 1},{"smoldering": 123}, loc1)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'working_dir': None}
        ]

    def test_no_fires(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": []})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        assert _PR_COMPUTE_CALL_ARGS == []

    def test_one_fire(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        loc1 = FIRE['activity'][0]['active_areas'][0]['specified_points'][0]
        loc2 = FIRE['activity'][0]['active_areas'][1]['perimeter']
        assert _PR_COMPUTE_CALL_ARGS == [
            ({"foo": 1},{"smoldering": 123}, loc1),
            ({"bar": 2}, {"flaming": 434}, loc2)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'working_dir': None},
            {'working_dir': None}
        ]
        # TOOD: assert plumerise return value

class TestPlumeRiseRunSev(object):

    def setup(self):
        Config().set('sev', 'plumerise', 'model')
        self.fm = FiresManager()

    def test_fire_no_activity(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_NO_ACTIVITY]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == plumerise.NO_ACTIVITY_ERROR_MSG

    def test_fire_missing_location_area(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_LOCATION_AREA]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']

    def test_fire_missing_location_consumption(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_CONSUMPTION]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['sev']

        assert _PR_COMPUTE_CALL_ARGS == [
            ({"baz": 444},123)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'frp': None}
        ]


    def test_fire_missing_timeprofile(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_TIMEPROFILE]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['sev']

        assert _PR_COMPUTE_CALL_ARGS == [
            ({"baz": 444},123)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'frp': None}
        ]


    def test_fire_missing_start_time(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_START_TIME]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['sev']

        assert _PR_COMPUTE_CALL_ARGS == [
            ({"baz": 444}, 123)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'frp': None}
        ]

    # TODO: test with invalid start time


    def test_fire_missing_localmet(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_LOCALMET]})
        with raises(ValueError) as e_info:
            plumerise.run(self.fm)
        assert e_info.value.args[0] == plumerise.MISSING_LOCALMET_ERROR_MSG

    def test_no_fires(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": []})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        assert _PR_COMPUTE_CALL_ARGS == []

    def test_one_fire(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        loc1 = FIRE['activity'][0]['active_areas'][0]['specified_points'][0]
        loc2 = FIRE['activity'][0]['active_areas'][1]['perimeter']
        assert _PR_COMPUTE_CALL_ARGS == [
            ({"baz": 444}, 123),
            ({"bazoo": 555}, 3232)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'frp': None},
            {'frp': None}
        ]
        # TOOD: assert plumerise return value
