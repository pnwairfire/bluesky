"""Unit tests for bluesky.arlfinder"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import tempfile

from py.test import raises
from numpy.testing import assert_approx_equal

from bluesky.met import arlfinder

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
        assert m.pattern == '20141228|20141229|20141230|20141231|20150101|20150102|20150103|20150104'

        self.arl_finder._max_met_days_out = 1
        m = self.arl_finder._create_date_matcher(s,e)
        assert m.pattern == '20141231|20150101|20150102|20150103|20150104'