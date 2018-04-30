"""Unit tests for bluesky.datetimeutils"""

__author__ = "Joel Dubowy"

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
    @freeze_time("2016-01-14T13:01:11")
    def test_today_not_defined(self):
        # None value - leave as is
        assert datetimeutils.fill_in_datetime_strings(None) == None

        # invalid value - leave as is
        assert datetimeutils.fill_in_datetime_strings(123) == 123

        # string with nothing to replace
        assert datetimeutils.fill_in_datetime_strings("sljdfsd") == "sljdfsd"

        # invalid and thus not-replaceable
        assert datetimeutils.fill_in_datetime_strings("{today4}") == "{today4}"
        assert datetimeutils.fill_in_datetime_strings("{yesterday++1}") == "{yesterday++1}"
        assert datetimeutils.fill_in_datetime_strings("{timestamp++1}") == "{timestamp++1}"
        assert datetimeutils.fill_in_datetime_strings("{today--1:%Y}") == "{today--1:%Y}"

        # control codes outside of '{(today|tomorrow):' + '}'  and thus not replaced
        assert datetimeutils.fill_in_datetime_strings("%Y-%m-%d") == "%Y-%m-%d"

        # strings with replacements
        assert datetimeutils.fill_in_datetime_strings("{today}") == "20160114"
        assert datetimeutils.fill_in_datetime_strings("{today}00") == "2016011400"
        assert datetimeutils.fill_in_datetime_strings("{today+1}") == "20160115"
        assert datetimeutils.fill_in_datetime_strings("{today-4}") == "20160110"
        assert datetimeutils.fill_in_datetime_strings("{today-4}00") == "2016011000"
        assert datetimeutils.fill_in_datetime_strings("{yesterday+3}") == "20160116"
        assert datetimeutils.fill_in_datetime_strings("{yesterday-4}") == "20160109"
        assert datetimeutils.fill_in_datetime_strings("{yesterday-4}12") == "2016010912"
        assert datetimeutils.fill_in_datetime_strings("{timestamp+3}") == "20160117130111"
        assert datetimeutils.fill_in_datetime_strings("{timestamp-4}") == "20160110130111"
        assert datetimeutils.fill_in_datetime_strings("{timestamp-4}-0") == "20160110130111-0"
        assert datetimeutils.fill_in_datetime_strings("{today:%Y-%m-%d}") == "2016-01-14"
        assert datetimeutils.fill_in_datetime_strings("{today:%Y-%m-%d}T12Z") == "2016-01-14T12Z"
        assert datetimeutils.fill_in_datetime_strings("{today+2:%Y-%m-%d}") == "2016-01-16"
        assert datetimeutils.fill_in_datetime_strings("{today-2:%Y-%m-%d}") == "2016-01-12"
        assert datetimeutils.fill_in_datetime_strings("{today-3:%Y-%m-%d}T12Z") == "2016-01-11T12Z"
        assert datetimeutils.fill_in_datetime_strings("{yesterday:%Y-%m-%d}") == "2016-01-13"
        assert datetimeutils.fill_in_datetime_strings("{yesterday:%Y-%m-%d}T12Z") == "2016-01-13T12Z"
        assert datetimeutils.fill_in_datetime_strings("{yesterday+1:%Y-%m-%d}") == "2016-01-14"
        assert datetimeutils.fill_in_datetime_strings("{yesterday-4:%Y-%m-%d}") == "2016-01-09"
        assert datetimeutils.fill_in_datetime_strings("{yesterday-5:%Y-%m-%d}T12Z") == "2016-01-08T12Z"
        assert datetimeutils.fill_in_datetime_strings("{timestamp:%Y-%m-%dT%H}") == "2016-01-14T13"
        assert datetimeutils.fill_in_datetime_strings("{timestamp:%Y-%m-%d}T12Z") == "2016-01-14T12Z"
        assert datetimeutils.fill_in_datetime_strings("{timestamp+1:%Y-%m-%d}") == "2016-01-15"
        assert datetimeutils.fill_in_datetime_strings("{timestamp-4:%Y-%m-%d}") == "2016-01-10"
        assert datetimeutils.fill_in_datetime_strings("{timestamp-5:%Y-%m-%d}T12Z") == "2016-01-09T12Z"

        val = datetimeutils.fill_in_datetime_strings(
            "{today}-sdf-{yesterday:%Y-%m-%d}T12Z-%Y__%m-%d-{today:%m_%d}-"
            "{yesterday}-{sdf}-{today:%m%d%Y}-{yesterday:%m-%d-%Y}"
            "{today-2}=={today-3:%Y-%m-%d}-{yesterday-2}-{yesterday-3:%Y-%m-%d}"
            "{today+2}=={yesterday+2:%Y-%m-%d}"
            "%Y%m%dT%H%M%S"
            "{timestamp}")
        assert val == ("20160114-sdf-2016-01-13T12Z-%Y__%m-%d-01_14-"
            "20160113-{sdf}-01142016-01-13-2016"
            "20160112==2016-01-11-20160111-2016-01-10"
            "20160116==2016-01-15"
            "%Y%m%dT%H%M%S"
            "20160114130111")

    @freeze_time("2016-01-10T03:11:22")
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

        # invalid and thus not-replaceable
        assert datetimeutils.fill_in_datetime_strings("{today4}",
            today=datetime.date(2016, 2, 15)) == "{today4}"
        assert datetimeutils.fill_in_datetime_strings("{yesterday++1}",
            today=datetime.date(2016, 2, 15)) == "{yesterday++1}"
        assert datetimeutils.fill_in_datetime_strings("{timestamp++1}",
            today=datetime.date(2016, 2, 15)) == "{timestamp++1}"
        assert datetimeutils.fill_in_datetime_strings("{today--1:%Y}",
            today=datetime.date(2016, 2, 15)) == "{today--1:%Y}"

        # control codes outside of '{(today|tomorrow):' + '}'  and thus not replaced
        assert datetimeutils.fill_in_datetime_strings("%Y-%m-%d") == "%Y-%m-%d"

        # strings with replacements
        assert datetimeutils.fill_in_datetime_strings("{today}",
            today=datetime.date(2016, 2, 15)) == "20160215"
        assert datetimeutils.fill_in_datetime_strings("{today}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160215"

        assert datetimeutils.fill_in_datetime_strings("{today-1}",
            today=datetime.date(2016, 2, 15)) == "20160214"
        assert datetimeutils.fill_in_datetime_strings("{today-2}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160213"

        assert datetimeutils.fill_in_datetime_strings("{yesterday}",
            today=datetime.date(2016, 2, 15)) == "20160214"
        assert datetimeutils.fill_in_datetime_strings("{yesterday}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160214"

        assert datetimeutils.fill_in_datetime_strings("{yesterday-1}",
            today=datetime.date(2016, 2, 15)) == "20160213"
        assert datetimeutils.fill_in_datetime_strings("{yesterday-2}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160212"

        assert datetimeutils.fill_in_datetime_strings("{timestamp}",
            today=datetime.date(2016, 2, 15)) == "20160110031122"
        assert datetimeutils.fill_in_datetime_strings("{timestamp}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160110031122"

        assert datetimeutils.fill_in_datetime_strings("{timestamp-1}",
            today=datetime.date(2016, 2, 15)) == "20160109031122"
        assert datetimeutils.fill_in_datetime_strings("{timestamp-2}",
            today=datetime.datetime(2016, 2, 15, 1)) == "20160108031122"

        assert datetimeutils.fill_in_datetime_strings("{today:%Y-%m-%d}",
            today=datetime.date(2016, 2, 15)) == "2016-02-15"
        assert datetimeutils.fill_in_datetime_strings("{today:%Y-%m-%d}",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016-02-15"

        assert datetimeutils.fill_in_datetime_strings("{today-1:%Y-%m-%d}",
            today=datetime.date(2016, 2, 15)) == "2016-02-14"
        assert datetimeutils.fill_in_datetime_strings("{today-2:%Y-%m-%d}",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016-02-13"

        assert datetimeutils.fill_in_datetime_strings("{yesterday:%Y-%m-%d}",
            today=datetime.date(2016, 2, 15)) == "2016-02-14"
        assert datetimeutils.fill_in_datetime_strings("{yesterday:%Y-%m-%d}",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016-02-14"

        assert datetimeutils.fill_in_datetime_strings("{yesterday-1:%Y-%m-%d}",
            today=datetime.date(2016, 2, 15)) == "2016-02-13"
        assert datetimeutils.fill_in_datetime_strings("{yesterday-2:%Y-%m-%d}",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016-02-12"

        assert datetimeutils.fill_in_datetime_strings("{timestamp:%Y-%m-%d}",
            today=datetime.date(2016, 2, 15)) == "2016-01-10"
        assert datetimeutils.fill_in_datetime_strings("{timestamp:%Y-%m-%dT%H:%M:%S}",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016-01-10T03:11:22"

        assert datetimeutils.fill_in_datetime_strings("{timestamp-1:%Y-%m-%d}",
            today=datetime.date(2016, 2, 15)) == "2016-01-09"
        assert datetimeutils.fill_in_datetime_strings("{timestamp-2:%Y-%m-%dT%H:%M:%S}",
            today=datetime.datetime(2016, 2, 15, 1)) == "2016-01-08T03:11:22"

        val = datetimeutils.fill_in_datetime_strings(
            "{today}-sdf-{yesterday:%Y-%m-%d}T12Z-%Y__%m-%d-{today:%m_%d}-"
            "{yesterday}-{sdf}-{today:%m%d%Y}-{yesterday:%m-%d-%Y}"
            "{today-2}=={today-3:%Y-%m-%d}-{yesterday-2}-{yesterday-3:%Y-%m-%d}"
            "{today+2}=={yesterday+2:%Y-%m-%d}"
            "%Y%m%dT%H%M%S"
            "{timestamp}",
            today=datetime.date(2016, 1, 14))
        assert val == ("20160114-sdf-2016-01-13T12Z-%Y__%m-%d-01_14-"
            "20160113-{sdf}-01142016-01-13-2016"
            "20160112==2016-01-11-20160111-2016-01-10"
            "20160116==2016-01-15"
            "%Y%m%dT%H%M%S"
            "20160110031122")

class TestToDatetime(object):

    @freeze_time("2016-01-14")
    def test_date_not_defined(self):
        assert datetimeutils.to_datetime(None) == None

    @freeze_time("2016-01-14")
    def test_date_defined_as_invalid_value(self):
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime(123)
        assert e_info.value.args[0] == "Invalid datetime string value: 123"

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011412:11:00')
        assert e_info.value.args[0] == 'Invalid datetime string value: 2016011412:11:00'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011412:11:00Z')
        assert e_info.value.args[0] == 'Invalid datetime string value: 2016011412:11:00Z'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011312:11:00')
        assert e_info.value.args[0] == 'Invalid datetime string value: 2016011312:11:00'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2016011312:11:00Z')
        assert e_info.value.args[0] == 'Invalid datetime string value: 2016011312:11:00Z'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('today')
        assert e_info.value.args[0] == 'Invalid datetime string value: today'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('yesterday')
        assert e_info.value.args[0] == 'Invalid datetime string value: yesterday'

        # strftime control codes need to be replaced by call to
        # fill_in_datetime_strings, separately from  call to_datetime
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('%Y%m%d')
        assert e_info.value.args[0] == 'Invalid datetime string value: %Y%m%d'
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('%Y%m%d%H%M%S')
        assert e_info.value.args[0] == 'Invalid datetime string value: %Y%m%d%H%M%S'

        # '{today}' and '{yesterday}' need to be replaced by call to
        # fill_in_datetime_strings, separately from  call to_datetime
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('{today}')
        assert e_info.value.args[0] == 'Invalid datetime string value: {today}'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('{yesterday}')
        assert e_info.value.args[0] == 'Invalid datetime string value: {yesterday}'

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('1915-12-14T10:02:01', limit_range=True)
        assert e_info.value.args[0] == 'Invalid datetime string value: 1915-12-14T10:02:01 (outside of valid range)'
        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('2117-12-14T10:02:01', limit_range=True)
        assert e_info.value.args[0] == 'Invalid datetime string value: 2117-12-14T10:02:01 (outside of valid range)'

    @freeze_time("2016-01-14")
    def test_date_defined_as_date_string(self):
        dt = datetimeutils.to_datetime("20151214")
        assert dt == datetime.datetime(2015, 12, 14)

        dt = datetimeutils.to_datetime("2015-12-14T10:02:01")
        assert dt == datetime.datetime(2015, 12, 14, 10, 2, 1)

        dt = datetimeutils.to_datetime('20160114')
        assert dt == datetime.datetime(2016, 1, 14)

        with raises(BlueSkyDatetimeValueError) as e_info:
            datetimeutils.to_datetime('20160114121100')
        assert e_info.value.args[0] == "Invalid datetime string value: 20160114121100"

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('20160114121100Z')
        assert e_info.value.args[0] == "Invalid datetime string value: 20160114121100Z"

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

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('20160113121100')
        assert e_info.value.args[0] == "Invalid datetime string value: 20160113121100"

        with raises(BlueSkyDatetimeValueError) as e_info:
            dt = datetimeutils.to_datetime('20160113121100Z')
        assert e_info.value.args[0] == "Invalid datetime string value: 20160113121100Z"

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

        # distant past and future values are allowed as long as
        # kwarg 'limit_range' is left as False
        dt = datetimeutils.to_datetime("1915-12-14T10:02:01")
        assert dt == datetime.datetime(1915, 12, 14, 10, 2, 1)
        dt = datetimeutils.to_datetime("2117-12-14T10:02:01")
        assert dt == datetime.datetime(2117, 12, 14, 10, 2, 1)


    @freeze_time("2016-01-14")
    def test_date_defined_as_date_object(self):
        dt = datetimeutils.to_datetime(datetime.date(2015, 12, 14))
        assert dt == datetime.date(2015, 12, 14)

        dt = datetimeutils.to_datetime(datetime.datetime(2015, 12, 14, 2, 1, 23))
        assert dt == datetime.datetime(2015, 12, 14, 2, 1, 23)
