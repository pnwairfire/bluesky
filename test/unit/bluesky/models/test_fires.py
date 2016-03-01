"""Unit tests for bluesky.models.fires"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import json
import sys
import StringIO
import uuid

from py.test import raises
from numpy.testing import assert_approx_equal

from bluesky.models import fires

##
## Tests for Fire
##

class TestFire:

    def test_fills_in_id(self, monkeypatch):
        monkeypatch.setattr(uuid, "uuid1", lambda: "abcd1234")
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

    def test_fills_in_or_validates_type_and_fuel_type(self):
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
        assert e_info.value.message == fires.Fire.INVALID_TYPE_MSG.format('foo')

        f = fires.Fire()

        # validates 'type' on setattr
        with raises(ValueError) as e_info:
            f.type = 'foo'
        assert e_info.value.message == fires.Fire.INVALID_TYPE_MSG.format('foo')

        # validates 'type' on dict set
        with raises(ValueError) as e_info:
            f['type'] = 'foo'
        assert e_info.value.message == fires.Fire.INVALID_TYPE_MSG.format('foo')

        # validates 'fuel_type' on instantiation
        with raises(ValueError) as e_info:
            f = fires.Fire({"a": 123, "b": "sdf",
                "type": 'rx', 'fuel_type': 'bar'})
        assert e_info.value.message == fires.Fire.INVALID_FUEL_TYPE_MSG.format('bar')

        # validates 'fuel_type' on setattr
        with raises(ValueError) as e_info:
            f.fuel_type = 'bar'
        assert e_info.value.message == fires.Fire.INVALID_FUEL_TYPE_MSG.format('bar')

        # validates 'fuel_type' on dict set
        with raises(ValueError) as e_info:
            f['fuel_type'] = 'bar'
        assert e_info.value.message == fires.Fire.INVALID_FUEL_TYPE_MSG.format('bar')

    def test_accessing_attributes(self):
        f = fires.Fire({'a': 123, 'b': 'sdf'})
        assert 123 == f['a']
        assert 123 == f.a
        assert 'sdf' == f['b']
        assert 'sdf' == f.b
        with raises(KeyError) as e:
            f['sdfdsf']
        with raises(KeyError) as e:
            f.rifsijsflj

##
## Tests for FiresManager
##

class TestFiresManager:

    ## Get/Set Fires and Meta

    def test_getting_fires_and_meta(self):
        fires_manager = fires.FiresManager()
        fire_objects = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'})
        ]
        fires_manager._fires = {
            '1': [fire_objects[0]],
            '2': [fire_objects[1]]
        }
        fires_manager._fire_ids = ['1','2']
        fires_manager._meta = {'a':1, 'b':{'c':2}}

        assert fire_objects == fires_manager.fires
        assert 1 == fires_manager.a
        assert {'c':2} == fires_manager.b
        assert 2 == fires_manager.b['c']
        assert None == fires_manager.d

    def test_setting_fires_and_meta(self):
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

        assert set(['1','2']) == fires_manager._fire_ids
        assert {'1': [fire_objects[0]],'2': [fire_objects[1]]} == fires_manager._fires
        assert {'a':1, 'b':{'c':2}, 'd': 123} == fires_manager._meta == fires_manager.meta

    ## Loading

    def _stream(test_self, data=''):
        def _stream(self, file_name, flag):
            if flag == 'r':
                return StringIO.StringIO(data)
            else:
                test_self._output = StringIO.StringIO()
                return test_self._output
        return _stream

    def test_load_invalid_data(self, monkeypatch):
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

    def test_load_no_fires_no_meta(self, monkeypatch):
        fires_manager = fires.FiresManager()
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('{}'))
        fires_manager.loads()
        assert [] == fires_manager.fires
        assert {} == fires_manager.meta
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream('{"fire_information":[]}'))
        fires_manager.loads()
        assert [] == fires_manager.fires
        assert {} == fires_manager.meta

    def test_load_no_fires_with_meta(self, monkeypatch):
        fires_manager = fires.FiresManager()
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(
            '{"fire_information":[], "foo": {"bar": "baz"}}'))
        fires_manager.loads()
        assert [] == fires_manager.fires
        assert {"foo": {"bar": "baz"}} == fires_manager.meta

    def test_load_one_fire_with_meta(self, monkeypatch):
        fires_manager = fires.FiresManager()
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(
            '{"fire_information":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"}],'
            '"foo": {"bar": "baz"}}'))
        fires_manager.loads()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"})
        ]
        assert expected == fires_manager.fires
        assert {"foo": {"bar": "baz"}} == fires_manager.meta

    def test_load_multiple_fires_with_meta(self, monkeypatch):
        fires_manager = fires.FiresManager()
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream(
            '{"fire_information":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"},'
            '{"id":"b","bar":2, "baz": 1.1, "bee":"24.34"}],'
            '"foo": {"bar": "baz"}}'))
        fires_manager.loads()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        assert expected == fires_manager.fires
        assert {"foo": {"bar": "baz"}} == fires_manager.meta

    ## Dumping

    def test_dump_no_fire_no_meta(self, monkeypatch):
        pass

    def test_dump_no_fires_with_meta(self, monkeypatch):
        pass

    def test_dump_one_fire_with_meta(self, monkeypatch):
        pass

    def test_dump_multiple_fires_with_meta(self, monkeypatch):
        fires_manager = fires.FiresManager()
        monkeypatch.setattr(fires.FiresManager, '_stream', self._stream())
        fire_objects = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        fires_manager._fires = {
            '1': [fire_objects[0]],
            '2': [fire_objects[1]]
        }
        fires_manager._fire_ids = ['1','2']
        fires_manager._meta = {"foo": {"bar": "baz"}}

        fires_manager.dumps()
        expected = {
            "fire_information": fire_objects,
            "foo": {"bar": "baz"}
        }
        assert expected == json.loads(self._output.getvalue())

    # TODO: test instantiating with fires, dump, adding more with loads, dump, etc.

    ## Failures

    def test_fire_failure_handler(self):
        def go(fire):
            if fire.id == '2':
                raise RuntimeError("oops")

        # Skip
        fires_manager = fires.FiresManager()
        fires_manager.fires = [
            fires.Fire({'id': '1', 'name': 'n1'}),
            fires.Fire({'id': '2', 'name': 'n2'})
        ]
        fires_manager.config = {"skip_failed_fires": True}
        assert fires_manager.skip_failed_fires
        for fire in fires_manager.fires:
            with fires_manager.fire_failure_handler(fire):
                go(fire)
        assert fires_manager.fires == [
            fires.Fire({'id': '1', 'name': 'n1'})
        ]
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
        fires_manager.config = {"skip_failed_fires": False}
        assert not fires_manager.skip_failed_fires
        for fire in fires_manager.fires:
            if fire.id == '1':
                with fires_manager.fire_failure_handler(fire):
                    go(fire)
            else:
                with raises(RuntimeError) as e_info:
                    with fires_manager.fire_failure_handler(fire):
                        go(fire)
        assert len(fires_manager.fires) == 2
        assert fires_manager.fires[0] == fires.Fire({'id': '1', 'name': 'n1'})
        assert fires_manager.fires[1].id == '2'
        assert fires_manager.fires[1].name == 'n2'
        assert fires_manager.fires[1]['error']['message'] == 'oops'
        assert fires_manager.fires[1]['error']['traceback']
        assert fires_manager.failed_fires is None



##
## Tests for Merging
##
## TODO: unit test fires.FiresMerger directly
##

class TestFiresManagerMergeFires(object):

    def test_no_fires(self):
        fm = fires.FiresManager()
        assert fm.fires == []
        fm.merge_fires()
        assert fm.fires == []

    def test_one_fire(self):
        fm = fires.FiresManager()
        f = fires.Fire({'id': '1'})
        fm.fires = [f]
        assert fm.fires == [f]
        fm.merge_fires()
        assert fm.fires == [f]

    def test_none_to_merge(self):
        fm = fires.FiresManager()
        f = fires.Fire({'id': '1'})
        f2 = fires.Fire({'id': '2'})
        fm.fires = [f, f2]
        assert fm.fires == [f, f2]
        fm.merge_fires()
        assert fm.fires == [f, f2]

    def test_pre_ingestion(self):
        # test in both skip and no-skip modes
        for s in (True, False):
            # i.e. insufficient data to merge
            fm = fires.FiresManager()
            fm.set_config_value(s, 'merge', 'skip_failures')
            f = fires.Fire({'id': '1'})
            f2 = fires.Fire({'id': '1'})
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(fires.FiresMerger.INVALID_KEYS_MSG) > 0
            else:
                fm.merge_fires()
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.id))

    def test_post_fuelbeds(self):
        # test in both skip and no-skip modes
        for s in (True, False):
            # i.e. too much data to merge
            fm = fires.FiresManager()
            fm.set_config_value(s, 'merge', 'skip_failures')
            f = fires.Fire({'id': '1', 'location': {'area': 132}, 'fuelbeds': {}})
            f2 = fires.Fire({'id': '1', 'location': {'area': 132}, 'fuelbeds': {}})
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(fires.FiresMerger.INVALID_KEYS_MSG) > 0
            else:
                fm.merge_fires()
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.id))

    def test_differing_locations(self):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            fm.set_config_value(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1',
                'location': {
                    'area': 12,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            f2 = fires.Fire({
                'id': '1',
                'location': {
                    'area': 132,
                    'latitude': 47.0,
                    'longitude': -120.0
                }
            })
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(fires.FiresMerger.LOCATION_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                # Sort by area since ids are the same
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.location['area']))

    def test_growth_for_only_one_fire(self):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            fm.set_config_value(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1',
                'location': {
                    'area': 34,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            f2 = fires.Fire({
                'id': '1',
                "growth":[
                    {
                        "start": "2014-05-27T17:00:00",
                        "end": "2014-05-28T17:00:00",
                        "pct": 100.0
                    }
                ],
                'location': {
                    'area': 132,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(
                    fires.FiresMerger.GROWTH_FOR_BOTH_OR_NONE_MSG) > 0
            else:
                fm.merge_fires()
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.location['area']))

    def test_overlapping_growth(self):
        # TODO: implemented once check is in place
        pass

    def test_different_event_ids(self):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            fm.set_config_value(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1',
                "event_of":{
                    "id": "ABC"
                },
                'location': {
                    'area': 32,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            f2 = fires.Fire({
                'id': '1',
                "event_of":{
                    "id": "SDF"
                },
                'location': {
                    'area': 132,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(fires.FiresMerger.EVENT_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.location['area']))

    def test_different_fire_and_fuel_type(self):
        # test in both skip and no-skip modes
        for s in (True, False):
            fm = fires.FiresManager()
            fm.set_config_value(s, 'merge', 'skip_failures')
            f = fires.Fire({
                'id': '1',
                "type": "rx",
                "fuel_type": "natural",
                'location': {
                    'area': 23,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            f2 = fires.Fire({
                'id': '1',
                "type": "wf",
                "fuel_type": "natural",
                'location': {
                    'area': 132,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
            fm.fires = [f, f2]

            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(fires.FiresMerger.FIRE_TYPE_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.location['area']))

            f2.type = f.type
            f2.fuel_type = "activity"
            fm.fires = [f, f2]
            if not s:
                with raises(ValueError) as e_info:
                    fm.merge_fires()
                assert e_info.value.message.index(fires.FiresMerger.FUEL_TYPE_MISMATCH_MSG) > 0
            else:
                fm.merge_fires()
                assert [f, f2] == sorted(fm.fires, key=lambda e: int(e.location['area']))

    def test_merge_mixed_success_no_growth(self):
        fm = fires.FiresManager()
        #fm.set_config_value(True, 'merge', 'skip_failures')
        f = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural",
            'location': {
                'area': 50,
                'latitude': 45.2,
                'longitude': -120.0
            }
        })
        f2 = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural",
            'location': {
                'area': 132,
                'latitude': 45.2,
                'longitude': -120.0
            }
        })
        f3 = fires.Fire({
            'id': '2',
            "type": "rx",
            "fuel_type": "natural",
            'location': {
                'area': 136,
                'latitude': 45.0,
                'longitude': -120.0
            }
        })
        fm.fires = [f, f2, f3]
        fm.merge_fires()
        expected = [
            fires.Fire({
                'id': '1',
                "type": "rx",
                "fuel_type": "natural",
                'location': {
                    'area': 182.0,
                    'latitude': 45.2,
                    'longitude': -120.0
                }
            }),
            fires.Fire({
                'id': '2',
                "type": "rx",
                "fuel_type": "natural",
                'location': {
                    'area': 136,
                    'latitude': 45.0,
                    'longitude': -120.0
                }
            })
        ]
        assert expected == sorted(fm.fires, key=lambda e: int(e.id))

    def test_merge_mixed_success(self):
        fm = fires.FiresManager()
        #fm.set_config_value(True, 'merge', 'skip_failures')
        f = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural",
            'location': {
                'area': 90,
                'latitude': 45.0,
                'longitude': -120.0
            },
            "growth": [
                {
                    "start": "2014-05-28T17:00:00",
                    "end": "2014-05-29T17:00:00",
                    "pct": 60.0
                },
                {
                    "start": "2014-05-29T17:00:00",
                    "end": "2014-05-30T17:00:00",
                    "pct": 40.0
                }
            ]
        })
        f2 = fires.Fire({
            'id': '1',
            "type": "rx",
            "fuel_type": "natural",
            'location': {
                'area': 10,
                'latitude': 45.0,
                'longitude': -120.0
            },
            "growth": [
                {
                    "start": "2014-05-27T17:00:00",
                    "end": "2014-05-28T17:00:00",
                    "pct": 100.0
                }
            ]
        })
        f3 = fires.Fire({
            'id': '2',
            "type": "rx",
            "fuel_type": "natural",
            'location': {
                'area': 132,
                'latitude': 45.0,
                'longitude': -120.0
            },
            "growth": [
                {
                    "start": "2014-05-27T17:00:00",
                    "end": "2014-05-30T17:00:00",
                    "pct": 100.0
                }
            ]
        })
        fm.fires = [f, f2, f3]
        fm.merge_fires()
        expected = [
            fires.Fire({
                'id': '1',
                "type": "rx",
                "fuel_type": "natural",
                'location': {
                    'area': 100,
                    'latitude': 45.0,
                    'longitude': -120.0
                },
                "growth": [
                    {
                        "start": "2014-05-27T17:00:00",
                        "end": "2014-05-28T17:00:00",
                        "pct": 10.0
                    },
                    {
                        "start": "2014-05-28T17:00:00",
                        "end": "2014-05-29T17:00:00",
                        "pct": 54.0
                    },
                    {
                        "start": "2014-05-29T17:00:00",
                        "end": "2014-05-30T17:00:00",
                        "pct": 36.0
                    }
                ]
            }),
            fires.Fire({
                'id': '2',
                "type": "rx",
                "fuel_type": "natural",
                'location': {
                    'area': 132,
                    'latitude': 45.0,
                    'longitude': -120.0
                },
                "growth": [
                    {
                        "start": "2014-05-27T17:00:00",
                        "end": "2014-05-30T17:00:00",
                        "pct": 100.0
                    }
                ]
            })
        ]
        actual = sorted(fm.fires, key=lambda e: int(e.id))
        # assert growth precentages for fire id 1 separately, using
        # numpy's assert_approx_equal, to handle rounding errors
        for i in range(3):
            assert_approx_equal(
                expected[0].growth[i].pop('pct'),
                actual[0].growth[i].pop('pct'))
        assert expected == actual


##
## Tests for Filtering
##
## TODO: unit test fires.FiresFilter directly
##

class TestFiresManagerFilterFires(object):

    ## Filtering

    def test_no_filters_specified(self):
        # TODO: implement
        pass

    def test_filter_by_country(self):
        fm = fires.FiresManager()
        fm.fires = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '3', 'name': 'n3', 'country': "ZZ", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '5', 'name': 'n5', 'country': "USA", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '6', 'name': 'n6', 'country': '', 'bar1': 1 , 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'}),
            fires.Fire({'id': '9', 'name': 'n9', 'country': 'Unknown', 'bar2': 2 , 'baz':'baz2'}),
            fires.Fire({'id': '10', 'name': 'n10', "country": "USA", "barj": "jj", "baz": 99}),
            fires.Fire({'id': '11', 'name': 'n11', "country": "BZ", "barj": "jj", "baz": 99})
        ]


        fm.set_config_value([{}], 'filter', 'country')
        # TODO: assert raises self.FilterError(SPECIFY_WHITELIST_OR_BLACKLIST) if skip_failres == false
        # TODO: assert noop if skip_failres == true

        fm.set_config_value(["ZZ"], 'filter', 'country', 'blacklist')
        fm.set_config_value(["YY"], 'filter', 'country', 'whitelist')
        # TODO: assert raises self.FilterError(SPECIFY_WHITELIST_OR_BLACKLIST)error error if skip_failres == false
        # TODO: assert noop if skip_failres == true


        fm.set_config_value(["ZZ"], 'filter', 'country', 'blacklist')
        fm.set_config_value(None, 'filter', 'country', 'whitelist')
        fm.filter_fires()
        expected = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '5', 'name': 'n5', 'country': "USA", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '6', 'name': 'n6', 'country': '', 'bar1': 1 , 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'}),
            fires.Fire({'id': '9', 'name': 'n9', 'country': 'Unknown', 'bar2': 2 , 'baz':'baz2'}),
            fires.Fire({'id': '10', 'name': 'n10', "country": "USA", "barj": "jj", "baz": 99}),
            fires.Fire({'id': '11', 'name': 'n11', "country": "BZ", "barj": "jj", "baz": 99})
        ]
        assert expected == sorted(fm.fires, key=lambda e: int(e.id))

        fm.set_config_value(["USA", "CA", "UK", "BZ"],
            'filter', 'country', 'whitelist')
        fm.set_config_value(None, 'filter', 'country', 'blacklist')
        fm.filter_fires()
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '5', 'name': 'n5', 'country': "USA", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'}),
            fires.Fire({'id': '10', 'name': 'n10', "country": "USA", "barj": "jj", "baz": 99}),
            fires.Fire({'id': '11', 'name': 'n11', "country": "BZ", "barj": "jj", "baz": 99})
        ]
        assert expected == sorted(fm.fires, key=lambda e: int(e.id))

        fm.set_config_value(["USA"], 'filter', 'country', 'blacklist')
        fm.set_config_value(None, 'filter', 'country', 'whitelist')
        fm.filter_fires()
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'}),
            fires.Fire({'id': '11', 'name': 'n11', "country": "BZ", "barj": "jj", "baz": 99})
        ]
        assert expected == sorted(fm.fires, key=lambda e: int(e.id))

        fm.set_config_value(["USA", "CA", "UK"], 'filter', 'country', 'whitelist')
        fm.set_config_value(None, 'filter', 'country', 'blacklist')
        fm.filter_fires()
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'})
        ]
        assert expected == sorted(fm.fires, key=lambda e: int(e.id))

        fm.set_config_value(["USA", "CA"], 'filter', 'country', 'blacklist')
        fm.set_config_value(None, 'filter', 'country', 'whitelist')
        fm.filter_fires()
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
        ]
        assert expected == fm.fires

    def test_filter_by_area(self):
        fm = fires.FiresManager()
        fm.fires = [
            fires.Fire({'id': '1', 'location':{'area': 45}}),
            fires.Fire({'id': '2', 'location':{'area': 85}}),
            fires.Fire({'id': '3', 'location':{'area': 55}}),
            fires.Fire({'id': '4', 'location':{'area': 65}}),
            fires.Fire({'id': '5', 'location':{'area': 85}}),
            fires.Fire({'id': '6', 'location':{'area': 75}}),
            fires.Fire({'id': '7', 'location':{'area': 50}}),
            fires.Fire({'id': '8', 'location':{'area': 30}})
        ]
        # TDOD: both min and max
        # TDOD: min only
        # TDOD: max only

    def test_filter_by_location(self):
        # TDOD: ....
        pass
