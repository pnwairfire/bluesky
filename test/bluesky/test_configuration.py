"""Unit tests for bluesky.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser

from py.test import raises

from bluesky.configuration import (
    config_parser_from_dict,
    config_parser_to_dict,
    get_config_value
)


##
## Tests for Converting between dict and ConfigParser objects
##

class TestConfigParserFromDict(object):

    def test_none(self):
        c = config_parser_from_dict(None)
        assert isinstance(c, ConfigParser.ConfigParser)
        assert [] == c.sections()

    def test_empty(self):
        c = config_parser_from_dict({})
        assert isinstance(c, ConfigParser.ConfigParser)
        assert [] == c.sections()

    def test_invalid(self):
        with raises(ValueError) as e:
            c = config_parser_from_dict("sdf")
            # TODO: assert e's message

        with raises(ValueError) as e:
            c = config_parser_from_dict({'s': "sdf"})
            # TODO: assert e's message

    def test_valid(self):
        d = {
            'a': { 'aa': 'sdf', 'ab': "343"},
            'b': { 'ba': "123", 'bb': 'sdfs'}
        }
        c = config_parser_from_dict(d)
        assert isinstance(c, ConfigParser.ConfigParser)
        assert ['a','b'] == c.sections()
        assert 'sdf' == c.get('a', 'aa')
        assert "343" == c.get('a', 'ab')
        assert "123" == c.get('b', 'ba')
        assert 'sdfs' == c.get('b', 'bb')

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