import io

from py.test import raises

try:
    from bluesky.models import fires
except:
    import os
    import sys
    root_dir = os.path.abspath(os.path.join(sys.path[0], '../../../'))
    sys.path.insert(0, root_dir)
    from bluesky.models import fires

class TestFireDataFormats:
    def test_formats(self):
        assert set(['json', 'csv']) == set(fires.FireDataFormats.formats)

    def test_get_format_str(self):
        assert 'json' == fires.FireDataFormats.get_format_str(1)
        assert 'csv' == fires.FireDataFormats.get_format_str(2)
        assert None == fires.FireDataFormats.get_format_str(3)

    def test_format_attrs(self):
        assert 1 == fires.FireDataFormats.json
        assert 1 == fires.FireDataFormats.JSON
        with raises(fires.FireDataFormatNotSupported) as e:
            fires.FireDataFormats.sdf

class TestFire:

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

class TestFiresImporter:

    def test_from_json(self):
        fires_importer = fires.FiresImporter()
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u''))
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u'""'))
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u'"sdf"'))
        with raises(ValueError):
            fires_importer._from_json(io.StringIO(u'null'))

        expected = []
        assert expected == fires_importer._from_json(io.StringIO(u'[]'))
        expected.append({'foo':'a', 'bar':123})
        assert expected == fires_importer._from_json(io.StringIO(u'{"foo":a,"bar":123}'))
        assert expected == fires_importer._from_json(io.StringIO(u'[{"foo":a,"bar":123}]'))
        expected.append({'foo':'b', 'bar':2})
        assert expected == fires_importer._from_json(io.StringIO(u'[{"foo":a,"bar":123},{"foo":"b","bar":2}]'))



        # TODO: test case of single fire object
        # TODO: test case of non-empty array of fire objects

    def test_from_csv(self):
        fires_importer = fires.FiresImporter()
        expected = []
        assert expected == fires_importer._from_csv(io.StringIO(u'foo,bar'))
        expected.append({'foo':'a', 'bar':123})
        assert expected == fires_importer._from_csv(io.StringIO(u'foo,bar\na,123'))
        expected.append({'foo':'b', 'bar':2})
        assert expected == fires_importer._from_csv(io.StringIO(u'foo,bar\na,123\nb,2'))
