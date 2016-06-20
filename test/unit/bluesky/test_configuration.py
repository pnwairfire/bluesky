"""Unit tests for bluesky.configuration"""

__author__ = "Joel Dubowy"

import configparser

from py.test import raises

from bluesky.configuration import (
    config_parser_to_dict,
    get_config_value,
    set_config_value,
    merge_configs,
    NO_KEYS_ERR_MSG,
    INVALID_CONFIG_ERR_MSG,
    MISSING_KEYS_ERR_MSG,
    CONFIG_CONFLICT
)
from bluesky.exceptions import BlueSkyConfigurationError


class TestConfigParserToDict(object):

    def test_none(self):
        d = config_parser_to_dict(None)
        assert {} == d

    def test_empty(self):
        d = config_parser_to_dict(configparser.ConfigParser())
        assert {} == d

    def test_valid(self):
        c = configparser.ConfigParser()
        c.add_section('a')
        c.add_section('b')
        c.set('a', 'aa', 'sdf')
        c.set('a', 'ab', "343")
        c.set('b', 'ba', "123")
        c.set('b', 'bb', 'sdfs')
        d = {
            'a': { 'aa': 'sdf', 'ab': "343"},
            'b': { 'ba': "123", 'bb': 'sdfs'}
        }
        assert d == config_parser_to_dict(c)

##
## Tests for utilitu methods
##

class TestGetConfigValue(object):

    def test_no_config(self):
        with raises(BlueSkyConfigurationError) as e_info:
            get_config_value(None)
        assert e_info.value.message == NO_KEYS_ERR_MSG

        assert None == get_config_value(None, 's')
        assert None == get_config_value(None, 's', 'sdf')
        assert 1 == get_config_value(None, 's', default=1)
        assert 1 == get_config_value(None, 's', 'sdf', default=1)

    def test_empty_config(self):
        with raises(BlueSkyConfigurationError) as e_info:
            get_config_value({})
        assert e_info.value.message == NO_KEYS_ERR_MSG

        assert None == get_config_value({}, 's')
        assert None == get_config_value({}, 's', 'sdf')
        assert 1 == get_config_value({}, 's', default=1)
        assert 1 == get_config_value({}, 's', 'sdf', default=1)

    def test_full(self):
        config = {
            'a': {
                'aa': 'sdf',
                'ab': 343
            },
            'b': {
                'ba': 123,
                'bb': 'sdfs',
                'cc': {
                    'ccc': "SDF"
                }
            },
            'c': 12
        }

        with raises(BlueSkyConfigurationError) as e_info:
            get_config_value(config)
        assert e_info.value.message == NO_KEYS_ERR_MSG

        assert None == get_config_value(config, 'z')
        assert None == get_config_value(config, 'z', 'b')
        assert None == get_config_value(config, 'a', 'b')
        assert None == get_config_value(config, 'b', 'cc', 'z')
        assert None == get_config_value(config, 'a', 'aa', 'z')
        assert 1 == get_config_value(config, 'z', default=1)
        assert 1 == get_config_value(config, 'z', 'b', default=1)
        assert 1 == get_config_value(config, 'a', 'b', default=1)
        assert 1 == get_config_value(config, 'b', 'cc', 'z', default=1)
        assert 1 == get_config_value(config, 'a', 'aa', 'z', default=1)

        assert 12 == get_config_value(config, 'c')
        assert 12 == get_config_value(config, 'c', default=1)
        assert {'aa': 'sdf','ab': 343} == get_config_value(config, 'a')
        assert {'aa': 'sdf','ab': 343} == get_config_value(config, 'a', default=1)
        assert 'sdf' == get_config_value(config, 'a', 'aa')
        assert 'sdf' == get_config_value(config, 'a', 'aa', default=1)
        assert 'sdf' == get_config_value(config['a'], 'aa')
        assert 'sdf' == get_config_value(config['a'], 'aa', default=1)
        assert 'SDF' == get_config_value(config, 'b', 'cc', 'ccc')
        assert 'SDF' == get_config_value(config, 'b', 'cc', 'ccc', default=1)

class TestSetConfigValue(object):

    def test_invalid_config(self):
        with raises(BlueSkyConfigurationError) as e_info:
            set_config_value(12, 3, '123')
        assert e_info.value.message == INVALID_CONFIG_ERR_MSG

    def test_no_keys(self):
        with raises(BlueSkyConfigurationError) as e_info:
            set_config_value({}, 32)
        assert e_info.value.message == MISSING_KEYS_ERR_MSG

    def test_basic(self):
        config = {}
        set_config_value(config, 123, 'a')
        assert config == {'a': 123}
        set_config_value(config, 321, 'b', 'c', 'd')
        assert config == {'a': 123, 'b': {'c': {'d': 321}}}

    def test_override_existing_value(self):
        config = {'a': 123, 'b': {'c': {'d': 321}}}
        set_config_value(config, 34, 'a')
        assert config == {'a': 34, 'b': {'c': {'d': 321}}}
        set_config_value(config, 123123, 'b', 'c', 'd')
        assert config == {'a': 34, 'b': {'c': {'d': 123123}}}

    def test_override_existing_dict(self):
        config = {'a': 123, 'b': {'c': {'d': 321}}}
        set_config_value(config, 34, 'b', 'c')
        assert config == {'a': 123, 'b': {'c': 34}}

class TestMergeConfigs(object):

    def test_invalid_configs(self):
        with raises(BlueSkyConfigurationError) as e_info:
            merge_configs(12, {'a': 1})
        assert e_info.value.message == INVALID_CONFIG_ERR_MSG

        with raises(BlueSkyConfigurationError) as e_info:
            merge_configs({'a': 1}, 12)
        assert e_info.value.message == INVALID_CONFIG_ERR_MSG

        with raises(BlueSkyConfigurationError) as e_info:
            merge_configs(12, 12)
        assert e_info.value.message == INVALID_CONFIG_ERR_MSG

    def test_conflicting_configs(self):
        with raises(BlueSkyConfigurationError) as e_info:
            merge_configs({'a': 'a'}, {'a': {'b': 'c'}})
        assert e_info.value.message == CONFIG_CONFLICT

        with raises(BlueSkyConfigurationError) as e_info:
            merge_configs({'a': {'b': 'c'}}, {'a': 'a'})
        assert e_info.value.message == CONFIG_CONFLICT

    def test_empty_both_configs(self):
        a = {}
        b = merge_configs(a, {})
        assert a == b == {}

    def test_empty_config(self):
        a = {}
        b = merge_configs(a, {'a': 123})
        assert a == b == {'a': 123}

    def test_empty_to_be_merged_config(self):
        a = {'a': 123}
        b = merge_configs(a, {})
        assert a == b == {'a': 123}

    def test_all(self):
        a = {'a': 123}
        b = merge_configs(a, {'b': {'c': 3}})
        assert a == b == {'a': 123, 'b': {'c': 3}}
        b = merge_configs(a, {'b': {'d': 5}})
        assert a == b == {'a': 123, 'b': {'c': 3, 'd': 5}}
        b = merge_configs(a, {'b': {'d': 19, 'e': 10}, 'f': 321})
        assert a == b == {'a': 123, 'b': {'c': 3, 'd': 19, 'e': 10}, 'f': 321}
