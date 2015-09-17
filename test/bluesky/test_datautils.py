"""Unit tests for bluesky.datautils"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

#from py.test import raises

from bluesky import datautils

class TestDeepMerge(object):

    def test_both_empty(self):
        a = {}
        b = {}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {}

    def test_one_of_two_empty(self):
        a = {'a':1}
        b = {}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':1}

        a = {}
        b = {'a':1}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':1}

    def test_non_nested(self):
        a = {'a':1, 'b':34}
        b = {'b':23, 'c':34343}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':1,'b':23, 'c':34343}

    def test_nested(self):
        a = {'a':{'a':1,'b':2},'c':2}
        b = {'a':{'s':1,'b':6},'b':9}
        new_a = datautils.deepmerge(a,b)
        assert new_a == a == {'a':{'a':1,'b':6, 's':1},'c':2,'b':9}
