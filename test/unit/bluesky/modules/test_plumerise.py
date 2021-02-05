"""Unit tests for bluesky.modules.findmetdata"""

__author__ = "Joel Dubowy"

import datetime
import os
import tempfile
import uuid

from py.test import raises
from plumerise import sev, feps
from pyairfire import osutils

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
                    "timeprofile": {"2015-01-20T17:00:00": {"foo": 1}},
                    "localmet": {"2015-01-20T17:00:00": {"baz": 444}}
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
                    "localmet": {"2015-01-20T17:00:00": {"baz": 444}}
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
                    "timeprofile": {"2015-01-20T17:00:00": {"foo": 1}},
                    "localmet": {"2015-01-20T17:00:00": {"baz": 444}}
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
                    "timeprofile": {"2015-01-20T17:00:00": {"foo": 1}}
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
                    "timeprofile": {"2015-01-20T17:00:00": {"foo": 1}},
                    "localmet": {"2015-01-20T17:00:00": {"baz": 444}}
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
                    "timeprofile": {"2015-01-20T17:00:00": {"bar": 2}},
                    "localmet": {"2015-01-20T17:00:00": {"bazoo": 555}}
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

TEMPFILE_DIRS = []
def monkeypatch_tempfile_mkdtemp(monkeypatch):
    def _mkdtemp():
        t = '/tmp/bluesky-plumerise-unittest-' + str(uuid.uuid4())
        os.makedirs(t)
        TEMPFILE_DIRS.append(t)
        return t
    monkeypatch.setattr(tempfile, 'mkdtemp', _mkdtemp)

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
        Config().set(False, 'skip_failed_fires')
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
        monkeypatch_tempfile_mkdtemp(monkeypatch)

        self.fm.load({"fires": [FIRE_MISSING_LOCALMET]})

        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        loc1 = FIRE_MISSING_LOCALMET['activity'][0]['active_areas'][0]['specified_points'][0]
        loc1.pop('plumerise')
        assert _PR_COMPUTE_CALL_ARGS == [
            ({"2015-01-20T17:00:00":{"foo": 1}},{"smoldering": 123}, loc1)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'working_dir': os.path.join(TEMPFILE_DIRS[-1], 'feps-plumerise-'+ FIRE_MISSING_LOCALMET.id)}
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
        monkeypatch_tempfile_mkdtemp(monkeypatch)

        self.fm.load({"fires": [FIRE]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['feps']
        loc1 = FIRE['activity'][0]['active_areas'][0]['specified_points'][0]
        loc2 = FIRE['activity'][0]['active_areas'][1]['perimeter']
        loc1.pop('plumerise')
        loc2.pop('plumerise')
        assert _PR_COMPUTE_CALL_ARGS == [
            ({"2015-01-20T17:00:00":{"foo": 1}},{"smoldering": 123}, loc1),
            ({"2015-01-20T17:00:00":{"bar": 2}}, {"flaming": 434}, loc2)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'working_dir': os.path.join(TEMPFILE_DIRS[-1], 'feps-plumerise-'+ FIRE.id)},
            {'working_dir': os.path.join(TEMPFILE_DIRS[-1], 'feps-plumerise-'+ FIRE.id)}
        ]
        # TOOD: assert plumerise return value

class TestPlumeRiseRunSev(object):

    def setup(self):
        Config().set('sev', 'plumerise', 'model')
        Config().set(False, 'skip_failed_fires')
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
            ({"2015-01-20T17:00:00":{"baz": 444}},123)
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
            ({"2015-01-20T17:00:00":{"baz": 444}},123)
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
            ({"2015-01-20T17:00:00":{"baz": 444}}, 123)
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
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['sev']
        assert _PR_COMPUTE_CALL_ARGS == []

    def test_one_fire(self, reset_config, monkeypatch):
        monkeypatch_plumerise_class(monkeypatch)

        self.fm.load({"fires": [FIRE]})
        plumerise.run(self.fm)

        assert _PR_ARGS == ()
        assert _PR_KWARGS == defaults._DEFAULTS['plumerise']['sev']
        loc1 = FIRE['activity'][0]['active_areas'][0]['specified_points'][0]
        loc2 = FIRE['activity'][0]['active_areas'][1]['perimeter']
        assert _PR_COMPUTE_CALL_ARGS == [
            ({"2015-01-20T17:00:00":{"baz": 444}}, 123),
            ({"2015-01-20T17:00:00":{"bazoo": 555}}, 3232)
        ]
        assert _PR_COMPUTE_CALL_KWARGS == [
            {'frp': None},
            {'frp': None}
        ]
        # TOOD: assert plumerise return value



class TestFepsMetParams(object):



    def test_full_localmet(self):
        localmet = {
            "2019-07-26T17:00:00": {
                "DSWF": [652.0],
                "HGTS": [2160.9021755576596,2202.722510766737,2244.720288241463],
                "HPBL": 100.0,
                "LHTF": [35.0],
                "PBLH": 57.4,
                "PRES": [770.0,766.0,761.0],
                "PRSS": 771.0,
                "RELH": [71.1204271543227,65.49793700855042,62.56461628539485],
                "RGHS": [0.0],
                "RH2M": None,
                "SHGT": 2360.0,
                "SHTF": [-42.3],
                "SPHU": [6.7,6.5,6.2],
                "T02M": 7.0,
                "TEMP": [9.3,10.0,9.9],
                "TO2M": None,
                "TPOT": [304.5,305.6,306.0],
                "TPP1": [0.0],
                "TPP3": None,
                "TPP6": None,
                "TPPA": None,
                "U10M": -0.21,
                "USTR": [0.03],
                "UWND": [-0.81,1.1,2.3],
                "V10M": -2.0,
                "VWND": [-6.0,-4.8,-3.9,-3.3,-2.6],
                "WDIR": [7.2,347.0,329.4,324.7,315.1],
                "WSPD": [6.0,4.9,4.5,4.0],
                "WWND": [48.2,-51.1,-87.1,-102.0],
                "dew_point": [4.286508045104142,3.771121273292181,3.0178799126392164,1.973449819773748],
                "lat": 46.7905,
                "lng": -121.7343,
                "pressure": [769.0,765.0,761.0,756.0],
                "pressure_at_surface": 771.0,
                "sunrise_hour": 6.0,
                "sunset_hour": -3.0,
                "utc_offset": -7.0
            },
            "2019-07-26T18:00:00": {
                "DSWF": [471.0],
                "HGTS": [2160.9021755576596,2202.722510766737,2244.720288241463,2297.4696175928293],
                "HPBL": 100.0,
                "LHTF": [17.1],
                "PBLH": 99.3,
                "PRES": [770.0,766.0,761.0],
                "PRSS": 771.0,
                "RELH": [66.7023772993133,64.16773336549186,60.743560201923245,57.27609444995706],
                "RGHS": [0.0],
                "RH2M": None,
                "SHGT": 2360.0,
                "SHTF": [-27.1],
                "SPHU": [6.2,6.2,5.9,5.6],
                "T02M": 4.9,
                "TEMP": [9.1,9.6,9.6,9.6],
                "TO2M": None,
                "TPOT": [304.2,305.2,305.7,306.1],
                "TPP1": [0.0],
                "TPP3": None,
                "TPP6": None,
                "TPPA": None,
                "U10M": -0.27,
                "USTR": [0.05],
                "UWND": [-0.76,1.2,2.3],
                "V10M": -3.0,
                "VWND": [-7.7,-6.5,-5.7,-5.0],
                "WDIR": [5.1,348.6,337.0,335.0,330.4,328.6],
                "WSPD": [7.7,6.6,6.1,5.5,4.9,4.3,3.6,3.0,2.9],
                "WWND": [85.5,-18.8,-45.8,-51.7,-51.0,-44.7,-34.1],
                "dew_point": [3.1711875719998375,3.0942696482732686,2.3108754850738364,1.4761425379726916],
                "lat": 46.7905,
                "lng": -121.7343,
                "pressure": [769.0,765.0,761.0,756.0,751.0,745.0,738.0,730.0,721.0],
                "pressure_at_surface": 771.0,
                "sunrise_hour": 6.0,
                "sunset_hour": -3.0,
                "utc_offset": -7.0
            }
        }

        params = plumerise.FepsMetParams(localmet).dict
        expected = {
            'max_humid': 71.1204271543227,
            'max_temp': 10.0,
            'max_wind': 7.7,
            'max_wind_aloft': 3.012125495393577,
            'min_humid': 57.27609444995706,
            'min_temp': 9.1,
            'min_wind': 2.9,
            'min_wind_aloft': 2.010994778710278,
            'sunrise_hour': 6.0,
            'sunset_hour': -3.0
        }
        assert params == expected

    def test_partial_localmet(self):
        localmet = {
            "2019-07-26T17:00:00": {
                "RELH": [71.1204271543227,65.49793700855042,62.56461628539485],
                "TEMP": [9.3,10.0,9.9],
                "U10M": -0.21,
                "V10M": -2.0,
                "WSPD": [6.0,4.9,4.5,4.0],
                #"sunrise_hour": 6.0,
                #"sunset_hour": -3.0,
                "utc_offset": -7.0
            },
            "2019-07-26T18:00:00": {
                #"RELH": [66.7023772993133,64.16773336549186,60.743560201923245,57.27609444995706],
                "TEMP": [9.1,9.6,9.6,9.6],
                "U10M": -0.27,
                #"V10M": -3.0,
                #"WSPD": [7.7,6.6,6.1,5.5,4.9,4.3,3.6,3.0,2.9],
                #"sunrise_hour": 6.0,
                "sunset_hour": -3.0,
                "utc_offset": -7.0
            }
        }

        params = plumerise.FepsMetParams(localmet).dict
        expected = {
            'max_humid': 71.1204271543227,
            'max_temp': 10.0,
            'max_wind': 6.0,
            'max_wind_aloft': 2.010994778710278,
            'min_humid': 62.56461628539485,
            'min_temp': 9.1,
            'min_wind': 4.0,
            'min_wind_aloft': 2.010994778710278,
            'sunset_hour': -3.0
        }
        assert params == expected

    def test_no_localmet(self):
        localmet = {}

        params = plumerise.FepsMetParams(localmet).dict
        expected = {}
        assert params == expected
