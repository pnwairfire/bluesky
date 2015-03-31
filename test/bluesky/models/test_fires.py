import io
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

    ## From JSON

    def test_from_json_invalid_data(self):
        fires_importer = fires.FiresImporter()
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u''))
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u'""'))
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u'"sdf"'))
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u'null'))

    def test_from_json_no_fires(self):
        fires_importer = fires.FiresImporter()
        expected = []
        fires_importer._from_json(io.StringIO(u'[]'))
        assert expected == fires_importer.fires

    def test_from_json_one_fire_single_object(self):
        fires_importer = fires.FiresImporter()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"})
        ]
        fires_importer._from_json(io.StringIO(
            u'{"id":"a","bar":123,"baz":12.32,"bee":"12.12"}'))
        assert expected == fires_importer.fires

    def test_from_json_one_fire_array(self):
        fires_importer = fires.FiresImporter()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"})
        ]
        fires_importer._from_json(io.StringIO(
            u'[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"}]'))
        assert expected == fires_importer.fires

    def test_from_json_multiple_fires(self):
        fires_importer = fires.FiresImporter()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}),
            fires.Fire({'id':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'})
        ]
        fires_importer._from_json(io.StringIO(
            u'[{"id":"a","bar":123,"baz":12.32,"bee":"12.12"},'
              '{"id":"b","bar":2, "baz": 1.1, "bee":"24.34"}]'))
        assert expected == fires_importer.fires


class TestFiresImporterLoadingAndDumping:

    # TODO: monkeypatch fires.FiresImporter._stream in setup to avoid redundancy

    def test_full_cycle(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        assert [] == fires_importer.fires

        fire_json = (
            u'[{"id":"dfdf","name":"sdfs","fooj":"j","barj":"jj","baz":99},'
            + u'{"id":"3j34","name":"sdfi3234l","fo":"j","ba":"jj","ba":199}]')
        fire_objects = [
            {"id":"dfdf","name":"sdfs","fooj":"j","barj":"jj","baz":99},
            {"id":"3j34","name":"sdfi3234l","fo":"j","ba":"jj","ba":199}
        ]

        def _stream(self, file_name, flag):
            if flag == 'r':
                return StringIO.StringIO(fire_json)
            else:
                self._output = getattr(self, 'output', StringIO.StringIO())
                return self._output
        monkeypatch.setattr(fires.FiresImporter, '_stream', _stream)

        fires_importer.loads()
        assert fire_objects == fires_importer.fires
        fires_importer._output = StringIO.StringIO()
        fires_importer.dumps()
        assert fire_objects == json.loads(fires_importer._output.getvalue())

class TestFiresImporterLowerLevelMethods:

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
