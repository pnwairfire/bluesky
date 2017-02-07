"""Unit tests for looking up ecoregion from lat/lng
"""

from py.test import raises

from bluesky.ecoregion.lookup import lookup_ecoregion
from bluesky.exceptions import BlueSkyGeographyValueError

class TestEcoregionLookup(object):

    def test_valid(self):
        assert 'western' == lookup_ecoregion(45, -118)
        assert 'southern' == lookup_ecoregion(32, -88)
        # TODO: add a boreal example


    def test_invalid(self):
        # TODO: raise specific exception in lookup_ecoregion and
        #   update this code with that exception class
        with raises(BlueSkyGeographyValueError) as e_info:
            lookup_ecoregion(28, -182)

        with raises(BlueSkyGeographyValueError) as e_info:
            lookup_ecoregion(99, -122)

        # water
        assert None == lookup_ecoregion(28, -88)

        # on land but outside of shapefile area
        assert None == lookup_ecoregion(19, -100)
