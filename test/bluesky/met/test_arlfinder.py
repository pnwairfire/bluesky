"""Unit tests for bluesky.arlfinder"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import tempfile

import StringIO # for monkeypatching
from py.test import raises
from numpy.testing import assert_approx_equal

from bluesky.met import arlfinder
from bluesky import io # for monkeypatching

##
## Tests for ArlFinder
##

INDEX_2015110200 = """filename,start,end,interval
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110100.f24-35_12hr02.arl,2015-11-02 00:00:00,2015-11-02 11:00:00,12
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f12-23_12hr01.arl,2015-11-02 12:00:00,2015-11-02 23:00:00,12
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f24-35_12hr02.arl,2015-11-03 00:00:00,2015-11-03 11:00:00,12
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f36-47_12hr03.arl,2015-11-03 12:00:00,2015-11-03 23:00:00,12
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f48-59_12hr04.arl,2015-11-04 00:00:00,2015-11-04 11:00:00,12
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f60-71_12hr05.arl,2015-11-04 12:00:00,2015-11-04 23:00:00,12
/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f72-83_12hr06.arl,2015-11-05 00:00:00,2015-11-05 11:00:00,12
"""

INDEX_2015110300 = """filename,start,end,interval
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110200.f24-35_12hr02.arl,2015-11-03 00:00:00,2015-11-03 11:00:00,12
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110300.f12-23_12hr01.arl,2015-11-03 12:00:00,2015-11-03 23:00:00,12
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110300.f24-35_12hr02.arl,2015-11-04 00:00:00,2015-11-04 11:00:00,12
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110300.f36-47_12hr03.arl,2015-11-04 12:00:00,2015-11-04 23:00:00,12
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110300.f48-59_12hr04.arl,2015-11-05 00:00:00,2015-11-05 11:00:00,12
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110300.f60-71_12hr05.arl,2015-11-05 12:00:00,2015-11-05 23:00:00,12
/path/to/NWRMC/4km/2015110300/wrfout_d3.2015110300.f72-83_12hr06.arl,2015-11-06 00:00:00,2015-11-06 11:00:00,12
"""

class TestARLFinder(object):
    def setup(self):
        self.arl_finder = arlfinder.ArlFinder(tempfile.mkdtemp())

    def test_create_date_matcher(self):
        s = datetime.datetime(2015, 1, 1, 14)
        e = datetime.datetime(2015, 1, 4, 2)
        m = self.arl_finder._create_date_matcher(s,e)
        assert m.pattern == '.*(20141228|20141229|20141230|20141231|20150101|20150102|20150103|20150104).*'

        self.arl_finder._max_days_out = 1
        m = self.arl_finder._create_date_matcher(s,e)
        assert m.pattern == '.*(20141231|20150101|20150102|20150103|20150104).*'

    def test_parse_index_files(self, monkeypatch):
        # _parse_index_files simply concatenates the lists returned by
        # _parse_index_file
        monkeypatch.setattr(self.arl_finder, '_parse_index_file',
            lambda i: [i+'a', i+'b'])
        expected = ['aa', 'ab', 'ba', 'bb']
        assert expected == self.arl_finder._parse_index_files(['a','b'])

    def test_parse_index_file(self, monkeypatch):
        monkeypatch.setattr(io.Stream, "_open_file",
            lambda s: StringIO.StringIO(INDEX_2015110200))
        monkeypatch.setattr(self.arl_finder, "_get_file_pathname",
            lambda i, n: n)
        expected = [
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110100.f24-35_12hr02.arl',
                'start': datetime.datetime(2015,11,2,0,0,0),
                'end': datetime.datetime(2015,11,2,11,0,0)
            },
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f12-23_12hr01.arl',
                'start': datetime.datetime(2015,11,2,12,0,0),
                'end': datetime.datetime(2015,11,2,23,0,0)
            },
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f24-35_12hr02.arl',
                'start': datetime.datetime(2015,11,3,0,0,0),
                'end': datetime.datetime(2015,11,3,11,0,0)
            },
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f36-47_12hr03.arl',
                'start': datetime.datetime(2015,11,3,12,0,0),
                'end': datetime.datetime(2015,11,3,23,0,0)
            },
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f48-59_12hr04.arl',
                'start': datetime.datetime(2015,11,4,0,0,0),
                'end': datetime.datetime(2015,11,4,11,0,0)
            },
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f60-71_12hr05.arl',
                'start': datetime.datetime(2015,11,4,12,0,0),
                'end': datetime.datetime(2015,11,4,23,0,0)
            },
            {
                'file': '/storage/NWRMC/4km/2015110200/wrfout_d3.2015110200.f72-83_12hr06.arl',
                'start': datetime.datetime(2015,11,5,0,0,0),
                'end': datetime.datetime(2015,11,5,11,0,0)
            }
        ]
        assert expected == self.arl_finder._parse_index_file('foo')

    def test_determine_files_per_hour(self):
        arl_files = [
            {
                'file': 'b',
                'start': datetime.datetime(2015,1,2,0,0,0),
                'end': datetime.datetime(2015,1,2,3,0,0)
            },
            {
                'file': 'c',
                'start': datetime.datetime(2015,1,2,3,0,0),
                'end': datetime.datetime(2015,1,2,5,0,0)
            },
            {
                'file': 'd',
                'start': datetime.datetime(2015,1,2,4,0,0),
                'end':  datetime.datetime(2015,1,2,6,0,0)
            },
            {
                'file': 'a',
                'start': datetime.datetime(2015,1,1,23,0,0),
                'end': datetime.datetime(2015,1,2,1,0,0)
            }
        ]

        expected = {
            datetime.datetime(2015,1,1,23,0,0): 'a',
            datetime.datetime(2015,1,2,0,0,0): 'b',
            datetime.datetime(2015,1,2,1,0,0): 'b',
            datetime.datetime(2015,1,2,2,0,0): 'b',
            datetime.datetime(2015,1,2,3,0,0): 'c',
            datetime.datetime(2015,1,2,4,0,0): 'd',
            datetime.datetime(2015,1,2,5,0,0): 'd',
            datetime.datetime(2015,1,2,6,0,0): 'd'
        }

        assert expected == self.arl_finder._determine_files_per_hour(arl_files)
