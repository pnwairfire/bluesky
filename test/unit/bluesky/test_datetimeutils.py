"""Unit tests for bluesky.datetimeutils"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

from freezegun import freeze_time
from py.test import raises

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
        assert datetimeutils.today_utc() == self.MN_4_20.date()
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_19
        assert datetimeutils.yesterday_utc() == self.MN_4_19.date()

    @freeze_time("2016-04-20 20:00:00", tz_offset=-8)
    def test_local_time_behind_but_same_day_as_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_20
        assert datetimeutils.today_utc() == self.MN_4_20.date()
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_19
        assert datetimeutils.yesterday_utc() == self.MN_4_19.date()

    @freeze_time("2016-04-21 03:00:00", tz_offset=-15)
    def test_local_time_day_before_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_21
        assert datetimeutils.today_utc() == self.MN_4_21.date()
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_20
        assert datetimeutils.yesterday_utc() == self.MN_4_20.date()

    @freeze_time("2016-04-20 04:00:00", tz_offset=8)
    def test_local_time_ahead_but_same_day_as_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_20
        assert datetimeutils.today_utc() == self.MN_4_20.date()
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_19
        assert datetimeutils.yesterday_utc() == self.MN_4_19.date()

    @freeze_time("2016-04-19 21:00:00", tz_offset=15)
    def test_local_time_day_ahead_of_utc(self):
        assert datetime.datetime.now() == self.NOON_4_20
        assert datetimeutils.today_midnight_utc() == self.MN_4_19
        assert datetimeutils.today_utc() == self.MN_4_19.date()
        assert datetimeutils.yesterday_midnight_utc() == self.MN_4_18
        assert datetimeutils.yesterday_utc() == self.MN_4_18.date()

class TestToDatetime(object):

    @freeze_time("2016-01-14")
    def test_date_not_defined(self):
        assert datetimeutils.to_datetime(None) == None

    @freeze_time("2016-01-14")
    def test_date_defined_as_invalid_value(self):
        with raises(ValueError) as e_info:
            dt = datetimeutils.to_datetime(123)
        assert e_info.value.message == "Invalid datetime string value: 123"

        with raises(ValueError) as e_info:
            dt = datetimeutils.to_datetime('{today}12:11:00')
        assert e_info.value.message == 'Invalid datetime string value: 2016011412:11:00'

        with raises(ValueError) as e_info:
            dt = datetimeutils.to_datetime('{today}12:11:00Z')
        assert e_info.value.message == 'Invalid datetime string value: 2016011412:11:00Z'


        with raises(ValueError) as e_info:
            dt = datetimeutils.to_datetime('{yesterday}12:11:00')
        assert e_info.value.message == 'Invalid datetime string value: 2016011312:11:00'

        with raises(ValueError) as e_info:
            dt = datetimeutils.to_datetime('{yesterday}12:11:00Z')
        assert e_info.value.message == 'Invalid datetime string value: 2016011312:11:00Z'


    @freeze_time("2016-01-14")
    def test_date_defined_as_date_string(self):
        dt = datetimeutils.to_datetime("20151214")
        assert dt == datetime.datetime(2015, 12, 14)

        dt = datetimeutils.to_datetime("2015-12-14T10:02:01")
        assert dt == datetime.datetime(2015, 12, 14, 10, 2, 1)

    @freeze_time("2016-01-14")
    def test_date_defined_as_date_object(self):
        dt = datetimeutils.to_datetime(datetime.date(2015, 12, 14))
        assert dt == datetime.date(2015, 12, 14)

        dt = datetimeutils.to_datetime(datetime.datetime(2015, 12, 14, 2, 1, 23))
        assert dt == datetime.datetime(2015, 12, 14, 2, 1, 23)

    @freeze_time("2016-01-14")
    def test_date_defined_as_today_or_yesterday_string(self):
        dt = datetimeutils.to_datetime('today')
        assert dt == datetime.date(2016, 1, 14)

        dt = datetimeutils.to_datetime('yesterday')
        assert dt == datetime.date(2016, 1, 13)

    @freeze_time("2016-01-14")
    def test_date_defined_with_strftime_codes_and_or_today_or_yesterday_wildcards(self):
        dt = datetimeutils.to_datetime('{today}')
        assert dt == datetime.datetime(2016, 1, 14)
        dt = datetimeutils.to_datetime('{today}121100')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('{today}121100Z')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('{today}T121100')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('{today}T121100Z')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)

        dt = datetimeutils.to_datetime('{today}T12:11:00')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('{today}T12:11:00Z')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('{today}T12')
        assert dt == datetime.datetime(2016, 1, 14, 12)
        dt = datetimeutils.to_datetime('{today}T12Z')
        assert dt == datetime.datetime(2016, 1, 14, 12)

        dt = datetimeutils.to_datetime('{yesterday}')
        assert dt == datetime.datetime(2016, 1, 13)
        dt = datetimeutils.to_datetime('{yesterday}121100')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('{yesterday}121100Z')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('{yesterday}T121100')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('{yesterday}T121100Z')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('{yesterday}T12:11:00')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('{yesterday}T12:11:00Z')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('{yesterday}T12')
        assert dt == datetime.datetime(2016, 1, 13, 12)
        dt = datetimeutils.to_datetime('{yesterday}T12Z')
        assert dt == datetime.datetime(2016, 1, 13, 12)

        # TODO: test datetime='%Y-%m-%dT12:00:00', etc.
