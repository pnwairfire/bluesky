"""Unit tests for bluesky.sun"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

from py.test import raises

from bluesky import sun

class TestSun(object):

    ## top level tests

    def test_seattle_2016_3_4(self, monkeypatch):
        # sunrise 6:43 AM
        # sunset 6:00 PM
        s = sun.Sun(lat=47.5724962,lng=-122.307817)
        d = datetime.datetime(2016,3,4)

        # In Seattle's offset (-8)
        assert s.sunrise(d, -8) == datetime.datetime(2016,3,4,6,45,51)
        assert s.sunset(d, -8) == datetime.datetime(2016,3,4,17,56,27)
        assert s.sunrise_hr(d, -8) == 7
        assert s.sunset_hr(d, -8) == 18
        # TODO: test s.solornoon

        # in offset +1
        assert s.sunrise(d, 1) == datetime.datetime(2016,3,4,15,45,51)
        assert s.sunset(d, 1) == datetime.datetime(2016,3,5,2,56,27)
        assert s.sunrise_hr(d, 1) == 16
        assert s.sunset_hr(d, 1) == 3
        # TODO: test s.solornoon

        # No offfset specifie (defaults to 0, UTC)
        assert s.sunrise(d) == datetime.datetime(2016,3,4,14,45,51)
        assert s.sunset(d) == datetime.datetime(2016,3,5,1,56,27)
        assert s.sunrise_hr(d) == 15
        assert s.sunset_hr(d) == 2
        # TODO: test s.solornoon

    def test_seattle_2016_8_4(self):
        # sunrise 5:51 AM
        # sunset 8:38 PM
        s = sun.Sun(lat=47.5724962,lng=-122.307817)
        d = datetime.datetime(2016,3,4)

    def test_aukland_2016_8_4(self):
        # sunrise ??? 7:09 AM
        # sunset ??? 7:56 PM
        pass

    ## test helper methods

    # TODO: test _calc
    # TODO: test _datetime_from_decimal_day

    def test_rounded_hour(self):
        s = sun.Sun(lat=47.5724962,lng=-122.307817)
        assert 3 == s._rounded_hour(datetime.datetime(2015,3,5,3,22,0))
        assert 4 == s._rounded_hour(datetime.datetime(2015,3,5,3,34,0))
        assert 0 == s._rounded_hour(datetime.datetime(2015,3,5,23,55,0))
