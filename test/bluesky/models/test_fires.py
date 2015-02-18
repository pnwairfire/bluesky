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
## Tests for FireDataFormats
##

class TestFireDataFormats:
    def test_formats(self):
        assert set(['json', 'csv']) == set(fires.FireDataFormats.formats)

    def test_format_ids(self):
        assert set([1,2]) == set(fires.FireDataFormats.format_ids)

    def test_get_item(self):
        # id to format key
        assert 'json' == fires.FireDataFormats[1]
        assert 'csv' == fires.FireDataFormats[2]
        with raises(fires.FireDataFormatNotSupported) as e:
            fires.FireDataFormats[3]
        # format key to id
        assert 1 == fires.FireDataFormats['JSON']
        assert 1 == fires.FireDataFormats['json']
        assert 2 == fires.FireDataFormats['CSV']
        assert 2 == fires.FireDataFormats['csv']
        with raises(fires.FireDataFormatNotSupported) as e:
            fires.FireDataFormats['sdf']

    def test_format_attrs(self):
        assert 1 == fires.FireDataFormats.json
        assert 1 == fires.FireDataFormats.JSON
        with raises(fires.FireDataFormatNotSupported) as e:
            fires.FireDataFormats.sdf

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

    ## From CSV

    def test_from_csv_no_fires(self):
        fires_importer = fires.FiresImporter()
        fires_importer._from_csv(io.StringIO(u'id,bar, baz, bee '))
        expected = []
        assert expected == fires_importer.fires

    def test_from_csv_one_fire(self):
        fires_importer = fires.FiresImporter()
        expected = [{'id':'a','name':"asd",'bar':123, 'baz': 23.23, 'bee': 23.23 }]
        fires_importer._from_csv(io.StringIO(
            u'id,name,bar, baz, bee \n a,asd, 123, 23.23,"23.23"'))
        assert expected == fires_importer.fires

    def test_from_csv_multiple_fires(self):
        fires_importer = fires.FiresImporter()
        expected = [
            fires.Fire({'id':'a', 'bar':123, 'baz': 23.23, 'bee': 23.23 }),
            fires.Fire({'id':'b', 'bar':2, 'baz':1.2, "bee": 12.23})
        ]
        fires_importer._from_csv(io.StringIO(
            u'id,bar, baz, bee \n a, 123, 23.23,"23.23"\nb,2, 1.2,"12.23"'))
        assert expected == fires_importer.fires

    ## To JSON

    def test_to_json(self):
        pass

    ## To CSV

    def test_to_csv(self):
        pass

class TestFiresImporterLoadingAndDumping:

    # TODO: monkeypatch fires.FiresImporter._stream in setup to avoid redundancy

    def test_full_cycle(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        def _stream(self, file_name, flag):
            if flag == 'r':
                self._calls = getattr(self, '_calls', 0) + 1
                return StringIO.StringIO(
                    u'id,name,foo%d,bar%d,baz \n'
                     'A-%d,Aname%d, %d, a%d,baz%d\n'
                     'B-%d,Bname%d, b%d,%d,baz%d' % (
                        self._calls, self._calls, self._calls, self._calls, self._calls, self._calls,
                        self._calls, self._calls, self._calls, self._calls, self._calls, self._calls)
                )
            else:
                self._output = getattr(self, 'output', StringIO.StringIO())
                return self._output
        monkeypatch.setattr(fires.FiresImporter, '_stream', _stream)

        assert [] == fires_importer.fires

        fires_importer.loads(format=fires.FireDataFormats.csv)
        expected = [
            fires.Fire({'id': 'A-1', 'name':'Aname1', 'foo1':1, 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': 'B-1', 'name':'Bname1', 'foo1': 'b1', 'bar1': 1 , 'baz':'baz1'})
        ]
        assert expected == fires_importer.fires

        fires_importer.loads(format=fires.FireDataFormats.csv)
        expected = [
            fires.Fire({'id': 'A-1', 'name':'Aname1', 'foo1':1, 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': 'B-1', 'name':'Bname1', 'foo1': 'b1', 'bar1': 1 , 'baz':'baz1'}),
            fires.Fire({'id': 'A-2', 'name' :'Aname2', 'foo2':2, 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': 'B-2', 'name' :'Bname2', 'foo2': 'b2', 'bar2': 2 , 'baz':'baz2'})
        ]
        assert expected == fires_importer.fires

        # Note that CSV output doesn't preserve input column order
        expected_lines = [
            set([
                ("id","A-1"),
                ("name","Aname1"),
                ("foo1", "1"),
                ("bar1", "a1"),
                ("baz", "baz1"),
                ("foo2",""),
                ("bar2", "")
            ]),
            set([
                ("id","B-1"),
                ("name","Bname1"),
                ("foo1", "b1"),
                ("bar1", "1"),
                ("baz", "baz1"),
                ("foo2",""),
                ("bar2", "")
            ]),
            set([
                ("id","A-2"),
                ("name","Aname2"),
                ("foo1", ""),
                ("bar1", ""),
                ("baz", "baz2"),
                ("foo2","2"),
                ("bar2", "a2")
            ]),
            set([
                ("id","B-2"),
                ("name","Bname2"),
                ("foo1", ""),
                ("bar1", ""),
                ("baz", "baz2"),
                ("foo2","b2"),
                ("bar2", "2")
            ])
        ]
        fires_importer.dumps(format=fires.FireDataFormats.csv)
        dumped_lines = fires_importer._output.getvalue().strip('\n').split('\n')
        headers = dumped_lines[0].split(',')
        dumped_lines = [set(zip(headers, dl.split(','))) for dl in dumped_lines[1:]]
        assert expected_lines == dumped_lines

        fires_importer._output = StringIO.StringIO()
        fires_importer.dumps()
        expected = [
            {'id': 'A-1', 'name':'Aname1', 'foo1':1, 'bar1':'a1', 'baz':'baz1'},
            {'id': 'B-1', 'name':'Bname1', 'foo1': 'b1', 'bar1': 1 , 'baz':'baz1'},
            {'id': 'A-2', 'name' :'Aname2', 'foo2':2, 'bar2':'a2', 'baz':'baz2'},
            {'id': 'B-2', 'name' :'Bname2', 'foo2': 'b2', 'bar2': 2 , 'baz':'baz2'}
        ]
        assert expected == json.loads(fires_importer._output.getvalue())

        def _new_json_stream(self, file_name, flag):
            if flag == 'r':
                return StringIO.StringIO(
                    u'{"id":"dfdf","name":"sdfs","fooj":"j","barj":"jj","baz":99}'
                 )
            else:
                self._output = getattr(self, 'output', StringIO.StringIO())
                return self._output
        monkeypatch.setattr(fires.FiresImporter, '_stream', _new_json_stream)

        fires_importer.loads(format=fires.FireDataFormats.json)
        expected = [
            fires.Fire({'id': 'A-1', 'name':'Aname1', 'foo1':1, 'bar1':'a1', 'baz':'baz1'}),
            fires.Fire({'id': 'B-1', 'name':'Bname1', 'foo1': 'b1', 'bar1': 1 , 'baz':'baz1'}),
            fires.Fire({'id': 'A-2', 'name' :'Aname2', 'foo2':2, 'bar2':'a2', 'baz':'baz2'}),
            fires.Fire({'id': 'B-2', 'name' :'Bname2', 'foo2': 'b2', 'bar2': 2 , 'baz':'baz2'}),
            fires.Fire({'id': 'dfdf', 'name': 'sdfs', "fooj": "j", "barj": "jj", "baz": 99})
        ]
        assert expected == fires_importer.fires

        # Again, Note that CSV output doesn't preserve input column order
        expected_lines = [
            set([
                ("id", "A-1"),
                ("name", "Aname1"),
                ("foo1", "1"),
                ("bar1", "a1"),
                ("baz", "baz1"),
                ("foo2", ""),
                ("bar2", ""),
                ("barj", ""),
                ("fooj", "")
            ]),
            set([
                ("id", "B-1"),
                ("name", "Bname1"),
                ("foo1", "b1"),
                ("bar1", "1"),
                ("baz", "baz1"),
                ("foo2", ""),
                ("bar2", ""),
                ("barj", ""),
                ("fooj", "")
            ]),
            set([
                ("id", "A-2"),
                ("name", "Aname2"),
                ("foo1", ""),
                ("bar1", ""),
                ("baz", "baz2"),
                ("foo2", "2"),
                ("bar2", "a2"),
                ("barj", ""),
                ("fooj", "")
            ]),
            set([
                ("id", "B-2"),
                ("name", "Bname2"),
                ("foo1", ""),
                ("bar1", ""),
                ("baz", "baz2"),
                ("foo2", "b2"),
                ("bar2", "2"),
                ("barj" ,""),
                ("fooj", "")
            ]),
            set([
                ("id", "dfdf"),
                ("name", "sdfs"),
                ("foo1", ""),
                ("bar1", ""),
                ("baz", "99"),
                ("foo2", ""),
                ("bar2", ""),
                ("barj" ,"jj"),
                ("fooj", "j")
            ])
        ]
        fires_importer._output = StringIO.StringIO()
        fires_importer.dumps(format=fires.FireDataFormats.csv)
        dumped_lines = fires_importer._output.getvalue().strip('\n').split('\n')
        headers = dumped_lines[0].split(',')
        dumped_lines = [set(zip(headers, dl.split(','))) for dl in dumped_lines[1:]]
        assert expected_lines == dumped_lines

    def test_dumping_nested_fire_to_csv(self, monkeypatch):
        fires_importer = fires.FiresImporter()
        def _stream(self, file_name, flag):
            if flag == 'r':
                return StringIO.StringIO(
                    u'[{"id": "A-1", "name":"Aname1", "foo1":1, "bar1":"a1", "baz":"baz1"}]'
                )
            else:
                self._output = getattr(self, 'output', StringIO.StringIO())
                return self._output
        monkeypatch.setattr(fires.FiresImporter, '_stream', _stream)

        fires_importer.fires = [
            fires.Fire({
                "start": "20140202T121223",
                "id": "sdfsdfsdfsdf",
                "name": "sfkjhsdkjfhsd",
                "blah": {
                    "foo": 1,
                    "bar": "abc",
                    "bas": {
                        "a": "b"
                    }
                }
            })
        ]
        expected_lines = [
            set([
                ("id", "sdfsdfsdfsdf"),
                ("name", "sfkjhsdkjfhsd"),
                ("start", "20140202T121223"),
                ("blah_foo", "1"),
                ("blah_bar", "abc"),
                ("blah_bas_a", "b")
            ])
        ]
        fires_importer.dumps(format=fires.FireDataFormats.csv)
        dumped_lines = fires_importer._output.getvalue().strip('\n').split('\n')
        headers = dumped_lines[0].split(',')
        dumped_lines = [set(zip(headers, dl.split(','))) for dl in dumped_lines[1:]]
        assert expected_lines == dumped_lines


class TestFiresImporterLowerLevelMethods:

    def test_nested_fire_to_csv(self):
        pass

    def test_flattened_fires(self):
        pass

    def test_flatten(self):
        d = {
            'a': 1,
            'c': {
                'a': 2,
                'b': {
                    'x': 5,
                    'y' : 10}
                },
            'd': [1, 2, 3]
        }
        new_d = {
            'a': 1,
            'c_a': 2,
            'c_b_x': 5,
            'd': [1, 2, 3],
            'c_b_y': 10
        }
        assert new_d == fires.FiresImporter()._flatten(d)
        assert new_d == fires.FiresImporter()._flatten(new_d)  # NOOP

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
