"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"

import copy
import datetime
import json
import sys
import io
import uuid

import freezegun

from py.test import raises
from numpy.testing import assert_approx_equal

from bluesky import __version__
from bluesky.config import Config, DEFAULTS
from bluesky.models import fires, activity


class TestFire(object):

    def test_fills_in_id(self, monkeypatch, reset_config):
        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")
        # if id is missing, the id is set to generated guid.
        # Note: id used to integrate start and/or end, if specified;
        #   this is no longer the case
        f = fires.Fire({"a": 123, "b": "sdf"})
        assert "abcd1234" == f["id"]
        f = fires.Fire({"a": 123, "b": "sdf", "start": "20120202 10:20:32"})
        assert "abcd1234" == f["id"]
        f = fires.Fire({"a": 123, "b": "sdf", "end": "20120922 10:20:32"})
        assert "abcd1234" == f["id"]
        f = fires.Fire({
            "a": 123, "b": "sdf",
            "start": "20120202 10:20:32", "end": "20120922T10:20:32"})
        assert "abcd1234" == f["id"]
        # if id exists, use it
        f = fires.Fire({
            "a": 123, "b": "sdf",
            "start": "20120202 10:20:32", "end": "20120922T10:20:32",
            "id": "sdkjfh2rkjhsdf"})
        assert "sdkjfh2rkjhsdf" == f["id"]

    def test_fills_in_or_validates_type_and_fuel_type(self, reset_config):
        # defaults 'type' and 'fuel_type
        f = fires.Fire({"a": 123, "b": "sdf"})
        assert f['type'] == fires.Fire.DEFAULT_TYPE
        assert f['fuel_type'] == fires.Fire.DEFAULT_FUEL_TYPE

        # accepts 'type' and 'fuel_type values if specified and valid
        f = fires.Fire({"a": 123, "b": "sdf",
            "type": 'rx', 'fuel_type': 'piles'})
        assert f['type'] == 'rx'
        assert f['fuel_type'] == 'piles'

        # converts to lowercase
        f = fires.Fire({"a": 123, "b": "sdf",
            "type": 'Rx', 'fuel_type': 'PILES'})
        assert f['type'] == 'rx'
        assert f['fuel_type'] == 'piles'


        # validates 'type' on instantiation
        with raises(ValueError) as e_info:
            f = fires.Fire({"a": 123, "b": "sdf",
                "type": 'foo', 'fuel_type': 'piles'})
        assert e_info.value.args[0] == fires.Fire.INVALID_TYPE_MSG.format('foo')

        f = fires.Fire()

        # validates 'type' on setattr
        with raises(ValueError) as e_info:
            f.type = 'foo'
        assert e_info.value.args[0] == fires.Fire.INVALID_TYPE_MSG.format('foo')

        # validates 'type' on dict set
        with raises(ValueError) as e_info:
            f['type'] = 'foo'
        assert e_info.value.args[0] == fires.Fire.INVALID_TYPE_MSG.format('foo')

        # validates 'fuel_type' on instantiation
        with raises(ValueError) as e_info:
            f = fires.Fire({"a": 123, "b": "sdf",
                "type": 'rx', 'fuel_type': 'bar'})
        assert e_info.value.args[0] == fires.Fire.INVALID_FUEL_TYPE_MSG.format('bar')

        # validates 'fuel_type' on setattr
        with raises(ValueError) as e_info:
            f.fuel_type = 'bar'
        assert e_info.value.args[0] == fires.Fire.INVALID_FUEL_TYPE_MSG.format('bar')

        # validates 'fuel_type' on dict set
        with raises(ValueError) as e_info:
            f['fuel_type'] = 'bar'
        assert e_info.value.args[0] == fires.Fire.INVALID_FUEL_TYPE_MSG.format('bar')

    def test_accessing_attributes(self, reset_config):
        f = fires.Fire({'a': 123, 'b': 'sdf'})
        assert 123 == f['a']
        assert 123 == f.a
        assert 'sdf' == f['b']
        assert 'sdf' == f.b
        with raises(KeyError) as e:
            f['sdfdsf']
        with raises(AttributeError) as e:
            f.rifsijsflj

    def test_start_and_end(self, reset_config):
        # no activity windows
        f = fires.Fire({})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # empty activity list
        f = fires.Fire({"activity": []})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # one activity window with no 'start'
        f = fires.Fire({"activity": [{}]})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # one activity window with None 'start'
        f = fires.Fire({"activity": [{'start': None}]})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # multiple activity windows with no 'start'
        f = fires.Fire({"activity": [{}, {}]})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # multiple activity windows with None 'start'
        f = fires.Fire({"activity": [{'start': None}, {'start': None}]})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # multiple activity windows with None 'end'
        f = fires.Fire({"activity": [{'active_areas': [{'end': None}, {'end': None}]}]})
        assert None == f.start
        assert None == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # one activity window with start defined
        f = fires.Fire({"activity": [{'active_areas': [{'start': "2014-05-27T17:00:00"}]}]})
        assert datetime.datetime(2014,5,27,17,0,0) == f.start
        assert datetime.datetime(2014,5,27,17,0,0) == f.start_utc
        assert None == f.end
        assert None == f.end_utc
        # one activity window with end defined
        f = fires.Fire({"activity": [{'active_areas': [{'end': "2014-05-27T17:00:00"}]}]})
        assert None == f.start
        assert None == f.start_utc
        assert datetime.datetime(2014,5,27,17,0,0) == f.end
        assert datetime.datetime(2014,5,27,17,0,0) == f.end_utc
        # multiple activity windows, some with 'start' defined, some with end
        # defined, out of order
        f = fires.Fire({"activity": [{'active_areas': [
            {'start': None, 'end': '2014-05-30T17:00:00'},
            {'start': "2014-05-29T17:00:00", 'end': None},
            {'start': "2014-05-27T17:00:00", 'end': '2014-05-27T17:00:00'},
            {'start': None, 'end': None}
            ]}]})
        assert datetime.datetime(2014,5,27,17,0,0) == f.start
        assert datetime.datetime(2014,5,27,17,0,0) == f.start_utc
        assert datetime.datetime(2014,5,30,17,0,0) == f.end
        assert datetime.datetime(2014,5,30,17,0,0) == f.end_utc

        # multiple activity windows, all with 'start' & 'end' defined, out of order
        f = fires.Fire({"activity": [{'active_areas': [
            {'start': "2014-05-29T17:00:00", 'end': "2014-05-30T17:00:00"},
            {'start': "2014-05-27T17:00:00", 'end': "2014-05-28T17:00:00"},
            {'start': "2014-05-28T17:00:00", 'end': "2014-05-29T17:00:00"}
            ]}]})
        assert datetime.datetime(2014,5,27,17,0,0) == f.start
        assert datetime.datetime(2014,5,30,17,0,0) == f.end
        assert datetime.datetime(2014,5,27,17,0,0) == f.start_utc
        assert datetime.datetime(2014,5,30,17,0,0) == f.end_utc
        # multiple activity windows, all with 'start' & 'end' defined, out of
        # order, with utc_offset defined
        f = fires.Fire({
            "activity": [
                {
                    'active_areas': [
                        {
                            "utc_offset": '-07:00',
                            'start': "2014-05-29T17:00:00",
                            'end': "2014-05-30T17:00:00"
                        },
                        {
                            "utc_offset": '-07:00',
                            'start': "2014-05-27T17:00:00",
                            'end': "2014-05-28T17:00:00"
                        },
                        {
                            "utc_offset": '-07:00',
                            'start': "2014-05-28T17:00:00",
                            'end': "2014-05-29T17:00:00"
                        }
                    ]
                }
            ]
        })
        assert datetime.datetime(2014,5,27,17,0,0) == f.start
        assert datetime.datetime(2014,5,30,17,0,0) == f.end
        assert datetime.datetime(2014,5,28,0,0,0) == f.start_utc
        assert datetime.datetime(2014,5,31,0,0,0) == f.end_utc

    TEST_FIRE = fires.Fire({
        'id': '1',
        'activity': [
            {
                'active_areas': [
                    {
                        "start": "2014-05-27T17:00:00",
                        "end": "2014-05-28T17:00:00",
                        'specified_points': [
                            {'area': 34, 'lat': 45.0, 'lng': -120.0},
                        ]
                    },
                    {
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {'area': 34, 'lat': 44.0, 'lng': -119.0},
                        ],
                        "perimeter": {
                            "polygon": [
                                [-122.45, 46.43],
                                [-122.39, 46.43],
                                [-122.39, 46.40],
                                [-122.45, 46.40],
                                [-122.45, 46.43]
                            ]
                        }
                    }
                ]
            },
            {
                'active_areas': [
                    {
                        "start": "2014-05-29T19:00:00",
                        "end": "2014-05-30T19:00:00",
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

    TEST_FIRE_NO_ACTIVITY = fires.Fire({
        'id': '2'
    })

    TEST_FIRE_ACTIVITY_NO_LOCATION_INFO = fires.Fire({
        'id': '1',
        'activity': [
            {
                'active_areas': [
                    {
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00"
                        # No location information
                    }
                ]
            }
        ]
    })

    TEST_FIRE_ACTIVITY_INVALID_SPECIFIED_POINTS = fires.Fire({
        'id': '1',
        'activity': [
            {
                'active_areas': [
                    {
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'specified_points': [
                            {'lat': 45.0, 'lng': -120.0}, # no area
                        ]
                    }
                ]
            }
        ]
    })

    TEST_FIRE_ACTIVITY_INVALID_PERIMETER = fires.Fire({
        'id': '1',
        'activity': [
            {
                'active_areas': [
                    {
                        "start": "2014-05-25T17:00:00",
                        "end": "2014-05-26T17:00:00",
                        'perimeter': {
                            # missing polygon
                            "foo": 123
                        }
                    }
                ]
            }
        ]
    })

    def test_active_areas(self):
        # no activity
        assert [] == self.TEST_FIRE_NO_ACTIVITY.active_areas

        # missing location information
        expected = [{
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00"
        }]
        actual = self.TEST_FIRE_ACTIVITY_NO_LOCATION_INFO.active_areas
        assert actual == expected

        # invalid specified points
        expected = [{
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'lat': 45.0, 'lng': -120.0}, # no area
            ]
        }]
        actual = self.TEST_FIRE_ACTIVITY_INVALID_SPECIFIED_POINTS.active_areas
        assert actual == expected

        # invalid active area
        expected = [{
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'perimeter': {
                # missing polygon
                "foo": 123
            }
        }]
        actual = self.TEST_FIRE_ACTIVITY_INVALID_PERIMETER.active_areas
        assert actual == expected

        # mixed activity
        expected = [{
            "start": "2014-05-27T17:00:00",
            "end": "2014-05-28T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 45.0, 'lng': -120.0},
            ]
        },
        {
            "start": "2014-05-25T17:00:00",
            "end": "2014-05-26T17:00:00",
            'specified_points': [
                {'area': 34, 'lat': 44.0, 'lng': -119.0}
            ],
            "perimeter": {
                "polygon": [
                    [-122.45, 46.43],
                    [-122.39, 46.43],
                    [-122.39, 46.40],
                    [-122.45, 46.40],
                    [-122.45, 46.43]
                ]
            }
        },
        {
            "start": "2014-05-29T19:00:00",
            "end": "2014-05-30T19:00:00",
            "perimeter": {
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        }]
        actual = self.TEST_FIRE.active_areas
        assert actual == expected

    def test_locations(self):
        # no activity
        assert [] == self.TEST_FIRE_NO_ACTIVITY.locations

        # missing location information
        with raises(ValueError) as e_info:
            self.TEST_FIRE_ACTIVITY_NO_LOCATION_INFO.locations
        assert e_info.value.args[0] == activity.ActiveArea.MISSING_LOCATION_INFO_MSG

        # invalid specified points
        with raises(ValueError) as e_info:
            self.TEST_FIRE_ACTIVITY_INVALID_SPECIFIED_POINTS.locations
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['specified_points']

        # invalid perimeter
        with raises(ValueError) as e_info:
            self.TEST_FIRE_ACTIVITY_INVALID_PERIMETER.locations
        assert e_info.value.args[0] == activity.INVALID_LOCATION_MSGS['perimeter']

        # mixed activity
        expected = [
            {'area': 34, 'lat': 45.0, 'lng': -120.0},
            {'area': 34, 'lat': 44.0, 'lng': -119.0},
            {
                "polygon": [
                    [-121.45, 47.43],
                    [-121.39, 47.43],
                    [-121.39, 47.40],
                    [-121.45, 47.40],
                    [-121.45, 47.43]
                ]
            }
        ]
        actual = self.TEST_FIRE.locations
        assert actual == expected


##
## Tests for FiresManager
##

class TestFiresManager(object):

    ## Get/Set Fires and Meta

    def test_getting_fires_and_meta(self, reset_config):
        fires_manager = fires.FiresManager()
        fire_objects = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'})
        ]
        fires_manager.fires = fire_objects
        fires_manager._meta = {'a':1, 'b':{'c':2}}

        assert fire_objects == fires_manager.fires
        assert 1 == fires_manager.a
        assert {'c':2} == fires_manager.b
        assert 2 == fires_manager.b['c']
        assert None == fires_manager.d

    @freezegun.freeze_time("2016-04-20")
    def test_setting_fires_and_meta(self, reset_config):
        fires_manager = fires.FiresManager()
        fire_objects = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'})
        ]
        fires_manager.fires = fire_objects
        fires_manager.a = 1
        fires_manager.b = {'c': 2}
        # you can also set meta data directly
        fires_manager.meta['d'] = 123

        assert fires_manager.num_fires == 2
        assert set(['1','2']) == set(list(fires_manager._fires.keys()))
        assert {'1': [fire_objects[0]],'2': [fire_objects[1]]} == fires_manager._fires
        assert fires_manager.today == freezegun.api.FakeDatetime(2016, 4, 20)
        expected_meta = {
            'a':1, 'b':{'c':2}, 'd': 123
        }
        assert expected_meta == fires_manager._meta == fires_manager.meta

    ## Properties

    @freezegun.freeze_time("2016-04-20")
    def test_toy_is_processed_for_wildcards(self, monkeypatch, reset_config):
        fm = fires.FiresManager()
        assert fm.today == datetime.datetime(2016,4,20)

        # test setting fm.today by load

        fm = fires.FiresManager()
        fm.load({'today': datetime.datetime(2012, 4,3,22,11)})
        assert fm.today == datetime.datetime(2012, 4,3,22,11)

        fm = fires.FiresManager()
        fm.load({'today': "2012-04-02T22:11:00Z"})
        assert fm.today == datetime.datetime(2012, 4,2,22,11)

        fm = fires.FiresManager()
        fm.load({'today': "{today}"})
        assert fm.today == datetime.datetime(2016, 4,20)

        fm = fires.FiresManager()
        fm.load({'today': "{yesterday}"})
        assert fm.today == datetime.datetime(2016, 4, 19)

        # TODO: any other possibilities ??

        # test setting fm.today by assignmentd

        fm = fires.FiresManager()
        fm.today = datetime.datetime(2016, 4, 1)
        assert fm.today == datetime.datetime(2016, 4, 1)

        fm = fires.FiresManager()
        fm.today = "2012-04-04T22:13:00Z"
        assert fm.today == datetime.datetime(2012, 4, 4, 22, 13)

        fm = fires.FiresManager()
        fm.today = "{today}"
        assert fm.today == datetime.datetime(2016, 4, 20)

        fm = fires.FiresManager()
        fm.today = "{yesterday}"
        assert fm.today == datetime.datetime(2016, 4, 19)

        # TODO: any other possibilities ??

    def test_run_id_is_mutable(self, monkeypatch, reset_config):
        monkeypatch.setattr(uuid, 'uuid4', lambda: "sdf123")

        fm = fires.FiresManager()
        # if not already set, run_id is set when accessed.
        # This initial guid can be overwritten
        assert fm.run_id == "sdf123"
        fm.run_id = "sdfsdfsdf"
        assert fm.run_id == "sdfsdfsdf"

        # if FiresManager.load doesn't set run_id, then it can still be set after
        fm = fires.FiresManager()
        assert fm.run_id == "sdf123"
        fm.load({})
        assert fm.run_id == "sdf123"
        fm.run_id = "sdfsdfsdf"
        assert fm.run_id == "sdfsdfsdf"

        fm = fires.FiresManager()
        assert fm.run_id == "sdf123"
        fm.load({'run_id': "ggbgbg"})
        assert fm.run_id == "ggbgbg"
        fm.run_id = "sdfsdfsdf"
        assert fm.run_id == "sdfsdfsdf"

        fm = fires.FiresManager()
        assert fm.run_id == "sdf123"
        fm.run_id = "eee"
        assert fm.run_id == "eee"
        fm.run_id = "sdfsdfsdf"
        assert fm.run_id == "sdfsdfsdf"

        # when you load, fm starts from scratch
        fm = fires.FiresManager()
        assert fm.run_id == "sdf123"
        fm.load({'run_id': "ggbgbg"})
        assert fm.run_id == "ggbgbg"

    def test_earliest_and_latest_times(self, reset_config):
        fm = fires.FiresManager()
        f1 = fires.Fire({
            'id': '1',
            'activity': [
                {
                    'active_areas': [
                        {
                            "start": "2014-05-27T17:00:00",
                            "end": "2014-05-28T17:00:00",
                            'specified_points': [
                                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                            ]
                        },
                        {
                            "start": "2014-05-25T17:00:00",
                            "end": "2014-05-26T17:00:00",
                            'specified_points': [
                                {'area': 34, 'lat': 45.0, 'lng': -120.0},
                            ]
                        }
                    ]
                }
            ]
        })
        f2 = fires.Fire({
            'id': '2',
            "activity":[
                {
                    'active_areas': [
                        {
                            "start": "2014-05-27T19:00:00",
                            "end": "2014-05-28T19:00:00",
                            'specified_points': [
                                {'area': 132, 'lat': 45.0, 'lng': -120.0},
                            ]
                        }
                    ]
                }
            ]
        })
        f3 = fires.Fire({
            'id': '2',
        })
        fm.fires = [f1, f2, f3]
        assert datetime.datetime(2014,5,25,17) == fm.earliest_start
        assert datetime.datetime(2014,5,28,19) == fm.latest_end

        # same thing, but with time zones specified for two of the fires
        f1.activity[0]['active_areas'][0]['utc_offset'] = '-07:00'
        f1.activity[0]['active_areas'][1]['utc_offset'] = '-07:00'
        f2.activity[0]['active_areas'][0]['utc_offset'] = '03:00' # no longer the latest time
        assert datetime.datetime(2014,5,26,0) == fm.earliest_start
        assert datetime.datetime(2014,5,29,0) == fm.latest_end

    ## Loading

    def _stream(test_self, data=''):
        def _stream(self, file_name, flag, compress=False):
            if flag.startswith('r'):
                return io.BytesIO(data.encode())
            else:
                test_self._output = io.StringIO()
                return test_self._output
        return _stream

    def test_load_invalid_data(self, monkeypatch, reset_config):
        fires_manager = fires.FiresManager()

        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(''))
        with raises(ValueError):
            fires_manager.loads()

        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('""'))
        with raises(ValueError):
            fires_manager.loads()

        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('"sdf"'))
        with raises(ValueError):
            fires_manager.loads()

        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('null'))
        with raises(ValueError):
            fires_manager.loads()

    @freezegun.freeze_time("2016-04-20")
    def test_load_no_fires_no_meta(self, monkeypatch, reset_config):
        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")

        fires_manager = fires.FiresManager()
        expected_meta = {}

        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('{}'))
        fires_manager.loads()
        assert fires_manager.num_fires == 0
        assert fires_manager.today == freezegun.api.FakeDatetime(2016,4,20)
        assert [] == fires_manager.fires
        assert expected_meta == fires_manager.meta

        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('{"fires":[]}'))
        fires_manager.loads()
        assert [] == fires_manager.fires
        assert expected_meta == fires_manager.meta

    @freezegun.freeze_time("2016-04-20")
    def test_load_no_fires_with_meta(self, monkeypatch, reset_config):
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(
            '{"fires":[], "foo": {"bar": "baz"}}'))
        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")

        fires_manager = fires.FiresManager()
        fires_manager.loads()
        assert fires_manager.num_fires == 0
        assert [] == fires_manager.fires
        assert fires_manager.today == freezegun.api.FakeDatetime(2016,4,20)
        expected_meta = {
            "foo": {"bar": "baz"}
        }
        assert expected_meta == fires_manager.meta

    @freezegun.freeze_time("2016-04-20")
    def test_load_one_fire_with_meta(self, monkeypatch, reset_config):
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(
            '{"fires":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"}],'
            '"foo": {"bar": "baz"}}'))
        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")

        fires_manager = fires.FiresManager()
        fires_manager.loads()
        expected_fires = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"})
        ]
        assert fires_manager.num_fires == 1
        assert expected_fires == fires_manager.fires
        assert fires_manager.today == freezegun.api.FakeDatetime(2016,4,20)
        expected_meta = {
            "foo": {"bar": "baz"}
        }
        assert expected_meta == fires_manager.meta

    @freezegun.freeze_time("2016-04-20")
    def test_load_multiple_fires_with_meta(self, monkeypatch, reset_config):
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(
            '{"fires":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"},'
            '{"id":"b","bar":2, "baz": 1.1, "bee":"24.34"}],'
            '"foo": {"bar": "baz"}}'))
        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")

        fires_manager = fires.FiresManager()
        fires_manager.loads()
        expected_fires = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        assert fires_manager.num_fires == 2
        assert expected_fires == fires_manager.fires
        assert fires_manager.today == freezegun.api.FakeDatetime(2016,4,20)
        expected_meta = {
            "foo": {"bar": "baz"},
        }
        assert expected_meta == fires_manager.meta

    @freezegun.freeze_time("2016-04-20")
    def test_load_multiple_streams(self, monkeypatch, reset_config):
        input_1 = io.StringIO('{"fires":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"},'
            '{"id":"b","bar":2, "baz": 1.1, "bee":"24.34"}],'
            '"foo": {"bar": "baz"}}')
        input_2 = io.StringIO('{"das": 1, "fires":[{"id":"c","bar":1223,"baz":1,"bee":"12"}]}')

        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")

        fires_manager = fires.FiresManager()
        fires_manager.loads(input_stream=input_1, append_fires=True)
        fires_manager.loads(input_stream=input_2, append_fires=True)
        expected_fires = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'}),
            fires.Fire({"id":"c", "bar":1223,"baz":1,"bee":"12"})
        ]
        assert fires_manager.num_fires == 3
        assert expected_fires == fires_manager.fires
        assert fires_manager.today == freezegun.api.FakeDatetime(2016,4,20)
        expected_meta = {
            "foo": {"bar": "baz"},
            "das": 1
        }
        assert expected_meta == fires_manager.meta


    ## Dumping

    def test_dump_no_fire_no_meta(self, monkeypatch, reset_config):
        pass

    def test_dump_no_fires_with_meta(self, monkeypatch, reset_config):
        pass

    def test_dump_one_fire_with_meta(self, monkeypatch, reset_config):
        pass

    @freezegun.freeze_time("2016-04-20")
    def test_dump_multiple_fires_with_meta(self, monkeypatch, reset_config):
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream())
        monkeypatch.setattr(uuid, "uuid4", lambda: "abcd1234")

        fires_manager = fires.FiresManager()
        fire_objects = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        fires_manager.fires = fire_objects
        fires_manager.foo = {"bar": "baz"}

        fires_manager.dumps()
        expected = {
            "run_id": "abcd1234",
            "today": "2016-04-20T00:00:00",
            "run_config": DEFAULTS,
            "fires": fire_objects,
            "foo": {"bar": "baz"},
            "counts": {
                "fires": 2,
                "failed_fires": 0,
                "locations": 0
            },
            "bluesky_version": __version__
        }

        actual = json.loads(self._output.getvalue())
        assert expected == actual

    # TODO: test instantiating with fires, dump, adding more with loads, dump, etc.

    ## Failures

    def test_fire_failure_handler(self, reset_config):
        def go(fire):
            if fire.id == '2':
                raise RuntimeError("oops")

        # Skip
        fires_manager = fires.FiresManager()
        fires_manager.fires = [
            fires.Fire({'id': '1', 'name': 'n1'}),
            fires.Fire({'id': '2', 'name': 'n2'})
        ]
        assert fires_manager.num_fires == 2
        Config().set({"skip_failed_fires": True})
        assert fires_manager.skip_failed_fires
        for fire in fires_manager.fires:
            with fires_manager.fire_failure_handler(fire):
                go(fire)
        assert fires_manager.fires == [
            fires.Fire({'id': '1', 'name': 'n1'})
        ]
        assert fires_manager.num_fires == 1
        assert len(fires_manager.failed_fires) == 1
        assert fires_manager.failed_fires[0].id == '2'
        assert fires_manager.failed_fires[0].name == 'n2'
        assert fires_manager.failed_fires[0]['error']['message'] == 'oops'
        assert fires_manager.failed_fires[0]['error']['traceback']

        # Don't Skip
        fires_manager = fires.FiresManager()
        fires_manager.fires = [
            fires.Fire({'id': '1', 'name': 'n1'}),
            fires.Fire({'id': '2', 'name': 'n2'})
        ]
        Config().set({"skip_failed_fires": False})
        assert fires_manager.num_fires == 2
        assert not fires_manager.skip_failed_fires
        for fire in fires_manager.fires:
            if fire.id == '1':
                with fires_manager.fire_failure_handler(fire):
                    go(fire)
            else:
                with raises(RuntimeError) as e_info:
                    with fires_manager.fire_failure_handler(fire):
                        go(fire)
        assert fires_manager.num_fires == 2
        assert len(fires_manager.fires) == 2
        assert fires_manager.fires[0] == fires.Fire({'id': '1', 'name': 'n1'})
        assert fires_manager.fires[1].id == '2'
        assert fires_manager.fires[1].name == 'n2'
        assert fires_manager.fires[1]['error']['message'] == 'oops'
        assert fires_manager.fires[1]['error']['traceback']
        assert fires_manager.failed_fires is None



class TestFiresManagerSettingToday(object):

    @freezegun.freeze_time("2016-04-20")
    def not_explicitly_set(self):
        fires_manager = fires.FiresManager()
        assert fires_manager.today == datetime.datetime(2016,4,20)

    @freezegun.freeze_time("2016-04-20")
    def test_set_to_string_in_loaded_input_data(self, reset_config):
        fires_manager = fires.FiresManager()
        fires_manager.load({"today": "2017-10-01"})
        assert fires_manager.today == datetime.datetime(2017,10,1)

    @freezegun.freeze_time("2016-04-20")
    def test_set_to_datetime_obj_in_loaded_input_data(self, reset_config):
        fires_manager = fires.FiresManager()
        fires_manager.load({"today": datetime.datetime(2017,10,1)})
        assert fires_manager.today == datetime.datetime(2017,10,1)

    @freezegun.freeze_time("2016-04-20")
    def test_set_to_date_obj_in_loaded_input_data(self, reset_config):
        fires_manager = fires.FiresManager()
        fires_manager.load({"today": datetime.date(2017,10,1)})
        assert fires_manager.today == datetime.datetime(2017,10,1)

    @freezegun.freeze_time("2016-04-20")
    def test_manually_set_to_string(self, reset_config):
        fires_manager = fires.FiresManager()
        fires_manager.today = "2017-10-01"
        assert fires_manager.today == datetime.datetime(2017,10,1)

    @freezegun.freeze_time("2016-04-20")
    def test_manually_set_to_datetime_obj(self, reset_config):
        fires_manager = fires.FiresManager()
        fires_manager.today = datetime.datetime(2017,10,1)
        assert fires_manager.today == datetime.datetime(2017,10,1)

    @freezegun.freeze_time("2016-04-20")
    def test_manually_set_to_date_obj(self, reset_config):
        fires_manager = fires.FiresManager()
        fires_manager.today = datetime.date(2017,10,1)
        assert fires_manager.today == datetime.datetime(2017,10,1)

    def test_is_mutable(self, reset_config):
        fires_manager = fires.FiresManager()

        # set to something other than UTC today (which is default)
        fires_manager.today = datetime.datetime(2017,10,1)
        assert fires_manager.today == datetime.datetime(2017,10,1)

        # set to same date (as datetime, date, and string objects)

        fires_manager.today = datetime.datetime(2017,10,1)
        assert fires_manager.today == datetime.datetime(2017,10,1)

        fires_manager.today = datetime.date(2017,10,1)
        assert fires_manager.today == datetime.datetime(2017,10,1)

        fires_manager.today = "2017-10-01T00:00:00"
        assert fires_manager.today == datetime.datetime(2017,10,1)

        fires_manager.today = "2017-10-01"
        assert fires_manager.today == datetime.datetime(2017,10,1)

        # set to different dates (as datetime, date, and string objects)

        fires_manager.today = datetime.datetime(2017,10,2)
        assert fires_manager.today == datetime.datetime(2017,10,2)

        fires_manager.today = datetime.date(2017,10,3)
        assert fires_manager.today == datetime.datetime(2017,10,3)

        fires_manager.today = "2017-10-04T00:00:00"
        assert fires_manager.today == datetime.datetime(2017,10,4)

        fires_manager.today = "2017-10-05"
        assert fires_manager.today == datetime.datetime(2017,10,5)
