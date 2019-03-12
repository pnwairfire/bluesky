"""Unit tests for bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import copy
import datetime

from py.test import raises

from bluesky.config import Config, DEFAULTS

class TestGetAndSet(object):

    def test_getting_defaults(self):
        # getting defaults
        assert Config.get() == DEFAULTS
        assert Config.get('skip_failed_fires') == False
        assert Config.get('fuelbeds', 'fccs_version') == '2'
        with raises(KeyError) as e:
            Config.get('sdfsd')
        with raises(KeyError) as e:
            Config.get('fuelbeds', 'sdf')
        with raises(KeyError) as e:
            Config.get('sdf', 'keep_heat')
        assert None == Config.get('sdf', allow_missing=True)
        assert None == Config.get('fuelbeds', 'sdf', allow_missing=True)
        assert None == Config.get('sdf', 'keep_heat', allow_missing=True)

    def test_setting_config_run_id_today(self):
        # setting
        Config.set({"foo": "{run_id}_{today-2:%Y%m%d}_bar", "bar": "baz"})
        assert Config._RUN_ID == None
        assert Config._TODAY == None
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today-2:%Y%m%d}_bar", bar="baz")
        EXPECTED = dict(DEFAULTS,
            foo="{run_id}_{today-2:%Y%m%d}_bar", bar="baz")
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        # set today
        Config.set_today(datetime.datetime(2019, 1, 5, 10, 12, 1))
        assert Config._RUN_ID == None
        assert Config._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today-2:%Y%m%d}_bar", bar="baz")
        EXPECTED = dict(DEFAULTS,
            foo="{run_id}_20190103_bar", bar="baz")
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        # set again; datetime wildcard should be filled in
        Config.set({"foo": "{run_id}_{today:%Y%m%d%H}_bar", "bar": "sdfsdf"})
        assert Config._RUN_ID == None
        assert Config._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today:%Y%m%d%H}_bar", bar="sdfsdf")
        EXPECTED = dict(DEFAULTS,
            foo="{run_id}_2019010510_bar", bar="dsfsdf")
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        # set run_id
        Config.set_run_id("abc123")
        assert Config._RUN_ID == "abc123"
        assert Config._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today:%Y%m%d%H}_bar", bar="sdfsdf")
        EXPECTED = dict(DEFAULTS,
            foo="abc123_2019010510_bar", bar="dsfsdf")
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        # set again; datetime and run_id wildcards should be filled in
        Config.set({"foo": "FOO_{run_id}_{today:%Y%m%d%H}_bar", "bar": "zz"})
        assert Config._RUN_ID == "abc123"
        assert Config._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="FOO_{run_id}_{today:%Y%m%d%H}_bar", bar="zz")
        EXPECTED = dict(DEFAULTS,
            foo="FOO_abc123_2019010510_bar", bar="zz")
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        # set in individual values
        Config.set(100, "bar")
        Config.set("sdfsdf{run_id}", "baz", "a")
        assert Config._RUN_ID == "abc123"
        assert Config._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="FOO_{run_id}_{today:%Y%m%d%H}_bar", bar=100,
            baz={"a": "sdfsdf{run_id}"})
        EXPECTED = dict(DEFAULTS,
            foo="FOO_abc123_2019010510_bar", bar=100,
            baz={"a": "sdfsdfabc123"})
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED


##
## Tests for setting aconfiguration (to make sure filecards get
## filled in, etc.) and merging
##

class TestMerge(object):

    def test_merge_configs(self):
        Config.merge({
            "foo": {"a": "{run_id}-{today}","b": 222,"c": 333,"d": 444}
        })
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": 222,"c": 333,"d": 444}
        })
        assert Config._RUN_ID == None
        assert Config._TODAY == None
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED_RAW # since today and now not set
        assert Config.get() == EXPECTED_RAW # since today and now not set

        Config.set_today(datetime.datetime(2019, 2, 4))
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": 222,"c": 333,"d": 444}
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-2019-02-04","b": 222,"c": 333,"d": 444}
        })
        assert Config._RUN_ID == None
        assert Config._TODAY == datetime.datetime(2019, 2, 4)
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        Config.merge({
            "foo": {"b": "{today-1}-{run_id}","c": 3333,"d": 4444,"bb": "bb"},
            "bar": {"b": "b"},
            "b": "b"
        })
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": "{today-1}-{run_id}",
                "c": 3333,"d": 4444,"bb": "bb"},
            "bar": {"b": "b"},
            "b": "b"
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-2019-02-04","b": "2019-02-03-{run_id}",
                "c": 3333,"d": 4444,"bb": "bb"},
            "bar": {"b": "b"},
            "b": "b"
        })
        assert Config._RUN_ID == None
        assert Config._TODAY == datetime.datetime(2019, 2, 4)
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        Config.merge({
            "foo": {"c": 33333,"d": 44444,"cc": "cc"},
            "baz": {"c": "c"},
            "c": "c"
        })
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": "{today-1}-{run_id}",
                "c": 33333,"d": 44444,"bb": "bb","cc": "cc"},
            "bar": {"b": "b"},
            "baz": {"c": "c"},
            "b": "b",
            "c": "c"
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-2019-02-04","b": "2019-02-03-{run_id}",
                "c": 33333,"d": 44444,"bb": "bb","cc": "cc"},
            "bar": {"b": "b"},
            "baz": {"c": "c"},
            "b": "b",
            "c": "c"
        })
        assert Config._RUN_ID == None
        assert Config._TODAY == datetime.datetime(2019, 2, 4)
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED

        Config.set_config_value("444444", 'foo', 'd')
        Config.set_config_value("dd", 'foo', 'dd')
        Config.set_config_value("d", 'boo', 'd')
        Config.set_config_value("d", 'd')
        Config.set_config_value(True, 'dbt')
        Config.set_config_value(False, 'dbf')
        Config.set_config_value(23, 'di')
        Config.set_config_value(123.23, 'df')
        Config.set_config_value('23', 'dci')
        Config.set_config_value('123.23', 'dcf')
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {
                "a": "{run_id}-{today}","b": "{today-1}-{run_id}",
                "c": 33333,"bb": "bb","cc": "cc","dd": "dd",
                "d": "444444" # because it was set on command line

            },
            "bar": {"b": "b"},
            "baz": {"c": "c"},
            "boo": {"d": "d"},
            "b": "b",
            "c": "c",
            "d": "d",
            "dbt": True,
            "dbf": False,
            "di": 23,
            "df": 123.23,
            "dci": "23",
            "dcf": "123.23"
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {
                "a": "{run_id}-2019-02-04","b": "2019-02-03-{run_id}",
                "c": 33333,"bb": "bb","cc": "cc","dd": "dd",
                "d": "444444" # because it was set on command line

            },
            "bar": {"b": "b"},
            "baz": {"c": "c"},
            "boo": {"d": "d"},
            "b": "b",
            "c": "c",
            "d": "d",
            "dbt": True,
            "dbf": False,
            "di": 23,
            "df": 123.23,
            "dci": "23",
            "dcf": "123.23"
        })
        assert Config._RUN_ID == None
        assert Config._TODAY == datetime.datetime(2019, 2, 4)
        assert Config._RAW_CONFIG == EXPECTED_RAW
        assert Config._CONFIG == EXPECTED
        assert Config.get() == EXPECTED
