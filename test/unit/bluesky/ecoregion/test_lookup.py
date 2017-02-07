"""Unit tests for looking up ecoregion from lat/lng
"""

from py.test import raises

from bluesky.ecoregion.lookup import lookup_ecoregion_shapely, lookup_ecoregion_ogr
from bluesky.exceptions import BlueSkyGeographyValueError

class TestLookupEcoregion(object):

    def test_valid(self):
        assert 'western' == lookup_ecoregion_shapely(45, -118)
        assert 'southern' == lookup_ecoregion_shapely(32, -88)
        # TODO: add a boreal example


    def test_invalid(self):
        # TODO: raise specific exception in lookup_ecoregion and
        #   update this code with that exception class
        with raises(BlueSkyGeographyValueError) as e_info:
            lookup_ecoregion_shapely(28, -182)

        with raises(BlueSkyGeographyValueError) as e_info:
            lookup_ecoregion_shapely(99, -122)

        # water
        assert None == lookup_ecoregion_shapely(28, -88)

        # on land but outside of shapefile area
        assert None == lookup_ecoregion_shapely(19, -100)

class TestLookupEcoregionOgr(object):

    def test_valid(self):
        assert 'western' == lookup_ecoregion_ogr(45, -118)
        assert 'southern' == lookup_ecoregion_ogr(32, -88)
        # TODO: add a boreal example


    def test_invalid(self):
        # TODO: raise specific exception in lookup_ecoregion and
        #   update this code with that exception class
        with raises(BlueSkyGeographyValueError) as e_info:
            lookup_ecoregion_ogr(28, -182)

        with raises(BlueSkyGeographyValueError) as e_info:
            lookup_ecoregion_ogr(99, -122)

        # water
        assert None == lookup_ecoregion_ogr(28, -88)

        # on land but outside of shapefile area
        assert None == lookup_ecoregion_ogr(19, -100)
