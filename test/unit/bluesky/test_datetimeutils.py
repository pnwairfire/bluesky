"""Unit tests for bluesky.datetimeutils"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

from freezegun import freeze_time

from bluesky import datetimeutils

class TestTodayAndYesterdayMidnight(object):

    NOON_4_20 = datetime.datetime(2016, 4, 20, 12, 0, 0)
    MN_4_18 = datetime.datetime(2016, 4, 18, 0, 0, 0)
    MN_4_19 = datetime.datetime(2016, 4, 19, 0, 0, 0)
    MN_4_20 = datetime.datetime(2016, 4, 20, 0, 0, 0)
    MN_4_21 = datetime.datetime(2016, 4, 21, 0, 0, 0)

    # Note: in call to freeze_time, specified time is UTC.

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_local_time_same_as_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_20
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_19

    @freeze_time("2016-04-20 20:00:00", tz_offset=-8)
    def test_local_time_behind_but_same_day_as_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_20
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_19

    @freeze_time("2016-04-21 03:00:00", tz_offset=-15)
    def test_local_time_day_before_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_21
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_20

    @freeze_time("2016-04-20 04:00:00", tz_offset=8)
    def test_local_time_ahead_but_same_day_as_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_20
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_19

    @freeze_time("2016-04-19 21:00:00", tz_offset=15)
    def test_local_time_day_ahead_of_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_19
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_18
