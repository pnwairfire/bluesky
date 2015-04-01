import json
import sys
import StringIO
import uuid

from py.test import raises

try:
    from bluesky.models import fires
except:
    import os

    root_dir = os.path.abspath(os.path.join(sys.path[0], '../../../'))
    sys.path.insert(0, root_dir)
    from bluesky.models import fires

##
## Tests for Fire
##

class TestFire:

    def test_fills_in_id(self, monkeypatch):
        monkeypatch.setattr(uuid, "uuid1", lambda: "abcd1234")
        # if start, end, and id are all missing, sets id to guid
        f = fires.Fire({"a": 123, "b": "sdf"})
        assert "abcd1234" == f["id"]
        assert "id" in f.auto_initialized_attrs
        # if start and/or end are specified but id is missing, sets id to guid
        # combined with start and/or end
        f = fires.Fire({"a": 123, "b": "sdf", "start": "20120202 10:20:32"})
        assert "abcd1234-2012020210:20:32" == f["id"]
        assert "id" in f.auto_initialized_attrs
        f = fires.Fire({"a": 123, "b": "sdf", "end": "20120922 10:20:32"})
        assert "abcd1234-2012092210:20:32" == f["id"]
        assert "id" in f.auto_initialized_attrs
        f = fires.Fire({
            "a": 123, "b": "sdf",
            "start": "20120202 10:20:32", "end": "20120922T10:20:32"})
        assert "abcd1234-2012020210:20:32-20120922T10:20:32" == f["id"]
        assert "id" in f.auto_initialized_attrs
        # if id exists, use it
        f = fires.Fire({
            "a": 123, "b": "sdf",
            "start": "20120202 10:20:32", "end": "20120922T10:20:32",
            "id": "sdkjfh2rkjhsdf"})
        assert "sdkjfh2rkjhsdf" == f["id"]
        assert "id" not in f.auto_initialized_attrs

    def test_fills_in_name(self, monkeypatch):
        monkeypatch.setattr(uuid, "uuid1", lambda: "abcd1234")
        # If name is missing, sets name to 'Unknown-' + id
        f = fires.Fire({"id": "SDFSDFSDF", "b": "sdf"})
        assert "Unknown-SDFSDFSDF" == f["name"]
        assert "name" in f.auto_initialized_attrs
        # If name is defined, leave it as is
        f = fires.Fire({"id": "SDFSDFSDF", "b": "sdf", "name": "sfkjhsdkjfhsd"})
        assert "sfkjhsdkjfhsd" == f["name"]
        assert "name" not in f.auto_initialized_attrs

    def test_fills_in_synonyms(self):
        f = fires.Fire({"date_time": "20140202T121223", "b": "sdf", "name": "sfkjhsdkjfhsd"})
        assert "20140202T121223" == f["date_time"] == f["start"]
        assert "start" in f.auto_initialized_attrs

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
## Tests for FiresImporter
##

class TestFiresImporter:

    ## Get/Set Fires and Meta

    def test_getting_fires_and_meta(self):
        fires_importer = fires.FiresImporter()
        fire_objects = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'})
        ]
        fires_importer._fires = {
            '1': fire_objects[0],
            '2': fire_objects[1]
        }
        fires_importer._fire_ids = ['1','2']
        fires_importer._meta = {'a':1, 'b':{'c':2}}

        assert fire_objects == fires_importer.fires
        assert 1 == fires_importer.a
        assert {'c':2} == fires_importer.b
        assert 2 == fires_importer.b['c']
        assert None == fires_importer.d

    def test_setting_fires_and_meta(self):
        fires_importer = fires.FiresImporter()
        fire_objects = [
            fires.Fire({'id': '1', 'name': 'n1', 'dfd':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '2', 'name': 'n2', 'bar':'a1', 'baz':'baz1'})
        ]
        fires_importer.fires = fire_objects
        fires_importer.a = 1
        fires_importer.b = {'c': 2}
        # you can also set meta data directly
        fires_importer.meta['d'] = 123

        assert ['1','2'] == fires_importer._fire_ids
        assert {'1': fire_objects[0],'2': fire_objects[1]} == fires_importer._fires
        assert {'a':1, 'b':{'c':2}, 'd': 123} == fires_importer._meta == fires_importer.meta

    ## Loading

    def _stream(self, data=''):
        def _stream(self, file_name, flag):
            if flag == 'r':
                return StringIO.StringIO(data)
            else:
                self._output = getattr(self, 'output', StringIO.StringIO())
                return self._output
        return _stream

    def test_load_invalid_data(self, monkeypatch):
        fires_importer = fires.FiresImporter()

        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream(''))
        with raises(ValueError):
            fires_importer.loads()

        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream('""'))
        with raises(ValueError):
            fires_importer.loads()

        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream('"sdf"'))
        with raises(ValueError):
            fires_importer.loads()

        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream('null'))
        with raises(ValueError):
            fires_importer.loads()

    def test_load_no_fires_no_meta(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream('{"fires":[]}'))
        fires_importer.loads()
        assert [] == fires_importer.fires
        assert {} == fires_importer.meta

    def test_load_no_fires_with_meta(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream(
            '{"fires":[], "foo": {"bar": "baz"}}'))
        fires_importer.loads()
        assert [] == fires_importer.fires
        assert {"foo": {"bar": "baz"}} == fires_importer.meta

    def test_load_one_fire_with_meta(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream(
            '{"fires":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"}],'
            '"foo": {"bar": "baz"}}'))
        fires_importer.loads()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"})
        ]
        assert expected == fires_importer.fires
        assert {"foo": {"bar": "baz"}} == fires_importer.meta

    def test_load_multiple_fires_with_meta(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream(
            '{"fires":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"},'
            '{"id":"b","bar":2, "baz": 1.1, "bee":"24.34"}],'
            '"foo": {"bar": "baz"}}'))
        fires_importer.loads()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        assert expected == fires_importer.fires
        assert {"foo": {"bar": "baz"}} == fires_importer.meta

    # ## Dumping

    def test_dump_no_fire_no_meta(self, monkeypatch):
        pass

    def test_dump_no_fires_with_meta(self, monkeypatch):
        pass

    def test_dump_one_fire_with_meta(self, monkeypatch):
        pass

    def test_dump_multiple_fires_with_meta(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        monkeypatch.setattr(fires.FiresImporter, '_stream', self._stream())
        fires = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        fires_importer._fires = {
            '1': fires[0],
            '2': fires[1]
        }
        fires_importer._fire_ids = ['1','2']
        fires_importer._meta = {"foo": {"bar": "baz"}}

        fires_importer.dumps()
        expected = ('{"fires":[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"},' +
            '{"id":"b","bar":2, "baz": 1.1, "bee":"24.34"}], "foo": {"bar": "baz"}}')
        assert expected == fires_importer._output.getvalue()

    # ## Filtering

    def test_filter(self):
        fires_importer = fires.FiresImporter()
        fires_importer.fires = [
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

        fires_importer.filter('country', blacklist=["ZZ"])
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
        assert expected == fires_importer.fires

        fires_importer.filter('country', whitelist=["USA", "CA", "UK", "BZ"])
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '5', 'name': 'n5', 'country': "USA", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'}),
            fires.Fire({'id': '10', 'name': 'n10', "country": "USA", "barj": "jj", "baz": 99}),
            fires.Fire({'id': '11', 'name': 'n11', "country": "BZ", "barj": "jj", "baz": 99})
        ]
        assert expected == fires_importer.fires

        fires_importer.filter('country', blacklist=["USA"])
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'}),
            fires.Fire({'id': '11', 'name': 'n11', "country": "BZ", "barj": "jj", "baz": 99})
        ]
        assert expected == fires_importer.fires

        fires_importer.filter('country', whitelist=["USA", "CA", "UK"])
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': '7', 'name': 'n7', 'country': "CA", 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': '8', 'name': 'n8', 'country': "CA", 'bar2':'adfsdf', 'baz':'baz2'})
        ]
        assert expected == fires_importer.fires

        fires_importer.filter('country', blacklist=["USA", "CA"])
        expected = [
            fires.Fire({'id': '4', 'name': 'n4', 'country': "UK", 'bar1':'a1', 'baz':'baz1'}),
        ]
        assert expected == fires_importer.fires

