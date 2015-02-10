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
            {'foo':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}
        ]
        fires_importer._from_json(io.StringIO(
            u'{"foo":"a","bar":123,"baz":12.32,"bee":"12.12"}'))
        assert expected == fires_importer.fires

    def test_from_json_one_fire_array(self):
        fires_importer = fires.FiresImporter()
        expected = [
            {'foo':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"}
        ]
        fires_importer._from_json(io.StringIO(
            u'[{"foo":"a","bar":123,"baz":12.32,"bee":"12.12"}]'))
        assert expected == fires_importer.fires

    def test_from_json_multiple_fires(self):
        fires_importer = fires.FiresImporter()
        expected = [
            {'foo':'a', 'bar':123, 'baz':12.32, 'bee': "12.12"},
            {'foo':'b', 'bar':2, 'baz': 1.1, 'bee': '24.34'}
        ]
        fires_importer._from_json(io.StringIO(
            u'[{"foo":"a","bar":123,"baz":12.32,"bee":"12.12"},'
              '{"foo":"b","bar":2, "baz": 1.1, "bee":"24.34"}]'))
        assert expected == fires_importer.fires

    def test_from_csv_no_fires(self):
        fires_importer = fires.FiresImporter()
        fires_importer._from_csv(io.StringIO(u'foo,bar, baz, bee '))
        expected = []
        assert expected == fires_importer.fires

    def test_from_csv_one_fire(self):
        fires_importer = fires.FiresImporter()
        expected = [{'foo':'a', 'bar':123, 'baz': 23.23, 'bee': 23.23 }]
        fires_importer._from_csv(io.StringIO(
            u'foo,bar, baz, bee \n a, 123, 23.23,"23.23"'))
        assert expected == fires_importer.fires

    def test_from_csv_multiple_fires(self):
        fires_importer = fires.FiresImporter()
        expected = [
            {'foo':'a', 'bar':123, 'baz': 23.23, 'bee': 23.23 },
            {'foo':'b', 'bar':2, 'baz':1.2, "bee": 12.23}
        ]
        fires_importer._from_csv(io.StringIO(
            u'foo,bar, baz, bee \n a, 123, 23.23,"23.23"\nb,2, 1.2,"12.23"'))
        assert expected == fires_importer.fires

    def test_to_json(self):
        pass

    def test_to_csv(self):
        pass

    def test_full_cycle(self):
        fires_importer = fires.FiresImporter()
