"""Unit tests for bluesky.datetimeutils"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

from freezegun import freeze_time
from py.test import raises

from bluesky import datetimeutils
from bluesky.exceptions import BlueSkyDatetimeValueError

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

class TestReplaceWildcards(object):
    @freeze_time("2016-01-14")
    def test_today_not_defined(self):
        # None value - leave as is
        assert datetimeutils.fill_in_datetime_strings(None) == None

        # invalid value - leave as is
        assert datetimeutils.fill_in_datetime_strings(123) == 123

        # string with nothing to replace
        assert datetimeutils.fill_in_datetime_strings("sljdfsd") == "sljdfsd"

        # strings with replacements
        assert datetimeutils.fill_in_datetime_strings("%Y%m%d00") == "2016011400"
        assert datetimeutils.fill_in_datetime_strings("%Y%m%d%H%M%S") == "20160114000000"
        assert datetimeutils.fill_in_datetime_strings("{today}") == "20160114"
        assert datetimeutils.fill_in_datetime_strings("{today}00") == "2016011400"
        assert datetimeutils.fill_in_datetime_strings("{yesterday}") == "20160113"
        assert datetimeutils.fill_in_datetime_strings("{yesterday}12") == "2016011312"

    @freeze_time("2016-01-14")
    def test_today_defined(self):
        # None value - leave as is
        assert datetimeutils.fill_in_datetime_strings(None,
            today=datetime.date(2016, 2, 15)) == None
        assert datetimeutils.fill_in_datetime_strings(None,
            today=datetime.datetime(2016, 2, 15, 0)) == None

        # invalid value - leave as is
        assert datetimeutils.fill_in_datetime_strings(123,
            today=datetime.date(2016, 2, 15)) == 123
        assert datetimeutils.fill_in_datetime_strings(123,
            today=datetime.datetime(2016, 2, 15,1)) == 123

        # string with nothing to replace
        assert datetimeutils.fill_in_datetime_strings("sljdfsd",
            today=datetime.date(2016, 2, 15)) == "sljdfsd"
        assert datetimeutils.fill_in_datetime_strings("sljdfsd",
            today=datetime.datetime(2016, 2, 15, 1)) == "sljdfsd"

        # strings with replacements
        assert datetimeutils.fill_in_datetime_strings("%Y%m%d00",
            today=datetime.date(2016, 2, 15)) == "2016021500"
        assert datetimeutils.fill_in_datetime_strings("%Y%m%d00",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016021500"

        assert datetimeutils.fill_in_datetime_strings("%Y%m%d%H%M%S",
            today=datetime.date(2016, 2, 15)) == "20160215000000"
        assert datetimeutils.fill_in_datetime_strings("%Y%m%d%H%M%S",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160215010000"

        assert datetimeutils.fill_in_datetime_strings("{today}",
            today=datetime.date(2016, 2, 15)) == "20160215"
        assert datetimeutils.fill_in_datetime_strings("{today}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160215"

        assert datetimeutils.fill_in_datetime_strings("{yesterday}",
            today=datetime.date(2016, 2, 15)) == "20160214"
        assert datetimeutils.fill_in_datetime_strings("{yesterday}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160214"

class TestToDatetime(object):

    @freeze_time("2016-01-14")
    def test_date_not_defined(self):
        assert datetimeutils.to_datetime(None) == None

    def test_date_defined_as_invalid_value(self):
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime(123)
        assert e_info.value.message == "Invalid datetime string value: 123"

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011412:11:00')
        assert e_info.value.message == 'Invalid datetime string value: 2016011412:11:00'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011412:11:00Z')
        assert e_info.value.message == 'Invalid datetime string value: 2016011412:11:00Z'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011312:11:00')
        assert e_info.value.message == 'Invalid datetime string value: 2016011312:11:00'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011312:11:00Z')
        assert e_info.value.message == 'Invalid datetime string value: 2016011312:11:00Z'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('today')
        assert e_info.value.message == 'Invalid datetime string value: today'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('yesterday')
        assert e_info.value.message == 'Invalid datetime string value: yesterday'

        # strftime control codes need to be replaced by call to
        # fill_in_datetime_strings, separately from  call to_datetime
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('%Y%m%d')
        assert e_info.value.message == 'Invalid datetime string value: %Y%m%d'
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('%Y%m%d%H%M%S')
        assert e_info.value.message == 'Invalid datetime string value: %Y%m%d%H%M%S'

        # '{today}' and '{yesterday}' need to be replaced by call to
        # fill_in_datetime_strings, separately from  call to_datetime
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('{today}')
        assert e_info.value.message == 'Invalid datetime string value: {today}'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('{yesterday}')
        assert e_info.value.message == 'Invalid datetime string value: {yesterday}'

    @freeze_time("2016-01-14")
    def test_date_defined_as_date_string(self):
        dt = datetimeutils.to_datetime("20151214")
        assert dt == datetime.datetime(2015, 12, 14)

        dt = datetimeutils.to_datetime("2015-12-14T10:02:01")
        assert dt == datetime.datetime(2015, 12, 14, 10, 2, 1)

        dt = datetimeutils.to_datetime('20160114')
        assert dt == datetime.datetime(2016, 1, 14)
        dt = datetimeutils.to_datetime('20160114121100')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160114121100Z')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160114T121100')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160114T121100Z')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)

        dt = datetimeutils.to_datetime('20160114T12:11:00')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160114T12:11:00Z')
        assert dt == datetime.datetime(2016, 1, 14, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160114T12')
        assert dt == datetime.datetime(2016, 1, 14, 12)
        dt = datetimeutils.to_datetime('20160114T12Z')
        assert dt == datetime.datetime(2016, 1, 14, 12)

        dt = datetimeutils.to_datetime('20160113')
        assert dt == datetime.datetime(2016, 1, 13)
        dt = datetimeutils.to_datetime('20160113121100')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160113121100Z')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160113T121100')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160113T121100Z')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160113T12:11:00')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160113T12:11:00Z')
        assert dt == datetime.datetime(2016, 1, 13, 12, 11, 00)
        dt = datetimeutils.to_datetime('20160113T12')
        assert dt == datetime.datetime(2016, 1, 13, 12)
        dt = datetimeutils.to_datetime('20160113T12Z')
        assert dt == datetime.datetime(2016, 1, 13, 12)

        # TODO: test datetime='%Y-%m-%dT12:00:00', etc.

    @freeze_time("2016-01-14")
    def test_date_defined_as_date_object(self):
        dt = datetimeutils.to_datetime(datetime.date(2015, 12, 14))
        assert dt == datetime.date(2015, 12, 14)

        dt = datetimeutils.to_datetime(datetime.datetime(2015, 12, 14, 2, 1, 23))
        assert dt == datetime.datetime(2015, 12, 14, 2, 1, 23)
