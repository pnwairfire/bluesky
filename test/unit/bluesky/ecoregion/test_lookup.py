"""Unit tests for looking up ecoregion from lat/lng
"""

from py.test import raises

from bluesky.ecoregion.lookup import EcoregionLookup
from bluesky.exceptions import (
    BlueSkyGeographyValueError,
    BlueSkyConfigurationError
)

class TestInvalidimplementation():
    def test(self):
        with raises(BlueSkyConfigurationError) as e_info:
            EcoregionLookup(implementation='sdfsd')

class BaseLookupEcoregionTest():

    def test_valid(self):
        assert 'western' == self.ecoregion_lookup.lookup(45, -118)
        assert 'southern' == self.ecoregion_lookup.lookup(32, -88)
        assert 'boreal' == self.ecoregion_lookup.lookup(66, -149)

    def test_invalid(self):
        # TODO: raise specific exception in lookup_ecoregion and
        #   update this code with that exception class
        with raises(BlueSkyGeographyValueError) as e_info:
            self.ecoregion_lookup.lookup(28, -182)

        with raises(BlueSkyGeographyValueError) as e_info:
            self.ecoregion_lookup.lookup(99, -122)

        # water
        assert None == self.ecoregion_lookup.lookup(28, -88)

        # on land but outside of shapefile area
        assert None == self.ecoregion_lookup.lookup(19, -100)

class TestLookupEcoregionShapely(BaseLookupEcoregionTest):

    def setup(self):
        self.ecoregion_lookup = EcoregionLookup(implementation='shapely')

class TestLookupEcoregionOgr(BaseLookupEcoregionTest):

    def setup(self):
        self.ecoregion_lookup = EcoregionLookup(implementation='ogr')
