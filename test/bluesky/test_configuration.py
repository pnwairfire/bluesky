"""Unit tests for bluesky.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser

from py.test import raises

from bluesky.configuration import (
    config_parser_to_dict,
    get_config_value
)


class TestConfigParserToDict(object):

    def test_none(self):
        d = config_parser_to_dict(None)
        assert {} == d

    def test_empty(self):
        d = config_parser_to_dict(ConfigParser.ConfigParser())
        assert {} == d

    def test_valid(self):
        c = ConfigParser.ConfigParser()
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
        assert None == get_config_value(None, 's')
        assert None == get_config_value(None, 's', 'sdf')
        assert 1 == get_config_value(None, 's', default=1)
        assert 1 == get_config_value(None, 's', 'sdf', default=1)

    def test_empty_config(self):
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
            }
        }

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

        assert {'aa': 'sdf','ab': 343} == get_config_value(config, 'a')
        assert {'aa': 'sdf','ab': 343} == get_config_value(config, 'a', default=1)
        assert 'sdf' == get_config_value(config, 'a', 'aa')
        assert 'sdf' == get_config_value(config, 'a', 'aa', default=1)
        assert 'sdf' == get_config_value(config['a'], 'aa')
        assert 'sdf' == get_config_value(config['a'], 'aa', default=1)
        assert 'SDF' == get_config_value(config, 'b', 'cc', 'ccc')
        assert 'SDF' == get_config_value(config, 'b', 'cc', 'ccc', default=1)