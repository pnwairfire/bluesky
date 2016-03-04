"""Unit tests for bluesky.sun"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

from py.test import raises

from bluesky import sun

class TestSun(object):

    def test_seattle_2016_03_04(self, monkeypatch):
        # sunrise 6:43 AM
        # sunset 6:00 PM
        s = sun.Sun(lat=47.5724962,lng=-122.307817)
        d = datetime.datetime(2016,3,4)

        # In Seattle's offset (-8)
        sunrise = s.sunrise(d, -8)
        assert sunrise.hour == 6
        assert sunrise.minute == 45
        sunset = s.sunset(d, -8)
        assert sunset.hour == 17
        assert sunset.minute == 56
        assert s.sunrise_hr(d, -8) == 7
        assert s.sunset_hr(d, -8) == 18
        # TODO: test solor noon with seattle's utc_offset

        # in offset +1
        sunrise = s.sunrise(d, 1)
        assert sunrise.hour == 15
        assert sunrise.minute == 45
        sunset = s.sunset(d, 1)
        assert sunset.hour == 2
        assert sunset.minute == 56
        assert s.sunrise_hr(d, 1) == 16
        assert s.sunset_hr(d, 1) == 3
        # TODO: test solor noon with London's utc_offset

        # No offfset specifie (defaults to 0, UTC)
        sunrise = s.sunrise(d)
        assert sunrise.hour == 14
        assert sunrise.minute == 45
        sunset = s.sunset(d)
        assert sunset.hour == 1
        assert sunset.minute == 56
        assert s.sunrise_hr(d) == 15
        assert s.sunset_hr(d) == 2
        # TODO: test solor noon with London's utc_offset

    def test_seattle_2016_08_04(self):
        # sunrise 5:51 AM
        # sunset 8:38 PM
        s = sun.Sun(lat=47.5724962,lng=-122.307817)
        d = datetime.datetime(2016,3,4)

    def test_aukland_2016_08_04(self):
        # sunrise 7:09 AM
        # sunset 7:56 PM
        pass
