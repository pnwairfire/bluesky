"""Unit tests for looking up ecoregion from lat/lng
"""

from py.test import raises

from bluesky.ecoregion import lookup

class TestEcoregionLookup(object):

    def test_valid(self):
        ecoregion = lookup_ecoregion(45, -122)
        # TODO: assert ecoregion is correct

    def test_file_doesnt_exist(self):
        # TODO: raise specific exception in lookup_ecoregion and
        #   update this code with that exception class
        with raises(Exception) as e_info:
            lookup(45, -130) # TODO: make sure this is in the ocean

        # TODO: another example on land but outside of shapefile area

