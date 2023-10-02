"""Unit tests for bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import copy
import datetime
import threading

from freezegun import freeze_time
from pytest import raises

from bluesky.config import Config, DEFAULTS, to_lowercase_keys

class TestToLowercaseKeys():

    def test(self):
        before = {
            "foo": "ERW",
            "BAR": 123,
            "BaZ": {
                'a': [
                    "SDF",
                    {
                        "C": 123,
                        "d": [
                            {
                                "asd": True,
                                "SDFSDF": 1
                            }
                        ],
                        "blueskykml_config": {
                            "CaseShouldBePreserved": {
                                "FooBar": 234
                            }
                        }
                    }
                ]
            }
        }
        before_copy = copy.deepcopy(before) # to make sure not done in place
        expected_after = {
            "foo": "ERW",
            "bar": 123,
            "baz": {
                'a': [
                    "SDF", # not a key, so should remain uppercase
                    {
                        "c": 123,
                        "d": [
                            {
                                "asd": True,
                                "sdfsdf": 1
                            }
                        ],
                        "blueskykml_config": {
                            "CaseShouldBePreserved": {
                                "FooBar": 234
                            }
                        }
                    }
                ]
            }
        }
        assert expected_after == to_lowercase_keys(before_copy)
        assert before == before_copy

    def test_conflicting_keys(self):
        # top level
        before = {
            "foo": "ERW",
            "BAR": 123,
            "Bar": {
                'a': 1
            }
        }
        with raises(ValueError) as e:
            to_lowercase_keys(before)

        # nested
        before = {
            "foo": "ERW",
            "BAR": 123,
            "Bdfd": {
                'a': 1,
                'A': 23
            }
        }
        with raises(ValueError) as e:
            to_lowercase_keys(before)


class TestGetAndSet():

    def setup_method(self):
        self._ORIGINAL_DEFAULTS = copy.deepcopy(DEFAULTS)

    def test_getting_defaults(self, reset_config):
        # getting defaults
        assert Config().get() == DEFAULTS
        assert Config().get('skip_failed_fires') == True
        assert Config().get('fuelbeds', 'fccs_version') == '2'
        # last key can be upper or lower
        assert Config().get('fuelbeds', 'FCCS_VERSION') == '2'
        with raises(KeyError) as e:
            Config().get('sdfsd')
        with raises(KeyError) as e:
            Config().get('fuelbeds', 'sdf')
        with raises(KeyError) as e:
            Config().get('sdf', 'keep_heat')
        assert None == Config().get('sdf', allow_missing=True)
        assert None == Config().get('fuelbeds', 'sdf', allow_missing=True)
        assert None == Config().get('sdf', 'keep_heat', allow_missing=True)

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_setting_config_run_id_today(self, reset_config):
        # setting
        Config().set({"FOO": "{run_id}_{today-2:%Y%m%d}_bar", "bar": "baz"})
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == None
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today-2:%Y%m%d}_bar", bar="baz")
        EXPECTED = dict(DEFAULTS,
            foo="{run_id}_20160418_bar", bar="baz")
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        # set today
        Config().set_today(datetime.datetime(2019, 1, 5, 10, 12, 1))
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today-2:%Y%m%d}_bar", bar="baz")
        EXPECTED = dict(DEFAULTS,
            foo="{run_id}_20190103_bar", bar="baz")
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        # set again; datetime wildcard should be filled in
        Config().set({"fOO": "{run_id}_{today:%Y%m%d%H}_bar", "bar": "sdfsdf"})
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today:%Y%m%d%H}_bar", bar="sdfsdf")
        EXPECTED = dict(DEFAULTS,
            foo="{run_id}_2019010510_bar", bar="sdfsdf")
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        # set run_id
        Config().set_run_id("abc123")
        assert Config()._data._RUN_ID == "abc123"
        assert Config()._data._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="{run_id}_{today:%Y%m%d%H}_bar", bar="sdfsdf")
        EXPECTED = dict(DEFAULTS,
            foo="abc123_2019010510_bar", bar="sdfsdf")
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        # set again; datetime and run_id wildcards should be filled in
        Config().set({"foo": "FOO_{run_id}_{today:%Y%m%d%H}_bar", "bar": "zz"})
        assert Config()._data._RUN_ID == "abc123"
        assert Config()._data._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="FOO_{run_id}_{today:%Y%m%d%H}_bar", bar="zz")
        EXPECTED = dict(DEFAULTS,
            foo="FOO_abc123_2019010510_bar", bar="zz")
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        # set in individual values
        Config().set(100, "bar")
        Config().set(200, "BAAAR")
        Config().set("sdfsdf{run_id}", "baz", "a")
        Config().set("{run_id}", "BAZ", "b")
        assert Config()._data._RUN_ID == "abc123"
        assert Config()._data._TODAY == datetime.datetime(2019,1,5,10,12,1)
        EXPECTED_RAW =  dict(DEFAULTS,
            foo="FOO_{run_id}_{today:%Y%m%d%H}_bar", bar=100, baaar=200,
            baz={"a": "sdfsdf{run_id}", "b": "{run_id}"})
        EXPECTED = dict(DEFAULTS,
            foo="FOO_abc123_2019010510_bar", bar=100, baaar=200,
            baz={"a": "sdfsdfabc123", "b": "abc123"})
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        assert self._ORIGINAL_DEFAULTS == DEFAULTS

##
## Tests for setting aconfiguration (to make sure filecards get
## filled in, etc.) and merging
##

class TestMerge():

    def setup_method(self):
        self._ORIGINAL_DEFAULTS = copy.deepcopy(DEFAULTS)

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_merge_configs(self, reset_config):
        Config().merge({
            "foo": {"A": "{run_id}-{today}","b": 222,"c": 333,"d": 444}
        })
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": 222,"c": 333,"d": 444}
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-20160420","b": 222,"c": 333,"d": 444}
        })
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == None
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        Config().set_today(datetime.datetime(2019, 2, 4))
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": 222,"c": 333,"d": 444}
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-20190204","b": 222,"c": 333,"d": 444}
        })
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == datetime.datetime(2019, 2, 4)
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        Config().merge({
            "foo": {"B": "{today-1}-{run_id}","c": 3333,"d": 4444,"bb": "bb"},
            "BAR": {"b": "b"},
            "b": "b"
        })
        EXPECTED_RAW = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-{today}","b": "{today-1}-{run_id}",
                "c": 3333,"d": 4444,"bb": "bb"},
            "bar": {"b": "b"},
            "b": "b"
        })
        EXPECTED = dict(DEFAULTS, **{
            "foo": {"a": "{run_id}-20190204","b": "20190203-{run_id}",
                "c": 3333,"d": 4444,"bb": "bb"},
            "bar": {"b": "b"},
            "b": "b"
        })
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == datetime.datetime(2019, 2, 4)
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        Config().merge({
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
            "foo": {"a": "{run_id}-20190204","b": "20190203-{run_id}",
                "c": 33333,"d": 44444,"bb": "bb","cc": "cc"},
            "bar": {"b": "b"},
            "baz": {"c": "c"},
            "b": "b",
            "c": "c"
        })
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == datetime.datetime(2019, 2, 4)
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        Config().set("444444", 'foo', 'd')
        Config().set("dd", 'foo', 'dd')
        Config().set("d", 'boo', 'd')
        Config().set("d", 'd')
        Config().set(True, 'dbt')
        Config().set(False, 'dbf')
        Config().set(23, 'di')
        Config().set(123.23, 'df')
        Config().set('23', 'dci')
        Config().set('123.23', 'dcf')
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
                "a": "{run_id}-20190204","b": "20190203-{run_id}",
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
        assert Config()._data._RUN_ID == None
        assert Config()._data._TODAY == datetime.datetime(2019, 2, 4)
        assert Config()._data._RAW_CONFIG == EXPECTED_RAW
        assert Config()._data._CONFIG == EXPECTED
        assert Config().get() == EXPECTED

        assert self._ORIGINAL_DEFAULTS == DEFAULTS


class TestThreadSafety():

    def test_getting_defaults(self, reset_config):


        class T(threading.Thread):
            def  __init__(self, i):
                super(T, self).__init__()
                self.i = i
                # we need to record exception in order to re-raise it
                # in the main thread
                self.exception = None

            def run(self):
                try:
                    # getting defaults
                    assert Config().get() == DEFAULTS
                    assert Config().get('skip_failed_fires') == True
                    Config().set(self.i, 'skip_failed_fires')
                    assert Config().get('skip_failed_fires') == self.i
                except Exception as e:
                    self.exception = e

        threads = []
        for i in range(2):
            t = T(i)
            t.start()
            threads.append(t)

        for t in threads:
            t.join()
            if t.exception:
                raise t.exception
