"""Unit tests for bluesky.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser

from py.test import raises

from bluesky import configuration


##
## Tests for Converting between dict and ConfigParser objects
##

class TestConfigParserFromDict(object):

    def test_none(self):
        c = configuration.config_parser_from_dict(None)
        assert isinstance(c, ConfigParser.ConfigParser)
        assert [] == c.sections()

    def test_empty(self):
        c = configuration.config_parser_from_dict({})
        assert isinstance(c, ConfigParser.ConfigParser)
        assert [] == c.sections()

    def test_invalid(self):
        with raises(ValueError) as e:
            c = configuration.config_parser_from_dict("sdf")
            # TODO: assert e's message

        with raises(ValueError) as e:
            c = configuration.config_parser_from_dict({'s': "sdf"})
            # TODO: assert e's message

    def test_valid(self):
        d = {
            'a': { 'aa': 'sdf', 'ab': "343"},
            'b': { 'ba': "123", 'bb': 'sdfs'}
        }
        c = configuration.config_parser_from_dict(d)
        assert isinstance(c, ConfigParser.ConfigParser)
        assert ['a','b'] == c.sections()
        assert 'sdf' == c.get('a', 'aa')
        assert "343" == c.get('a', 'ab')
        assert "123" == c.get('b', 'ba')
        assert 'sdfs' == c.get('b', 'bb')

class TestConfigParserToDict(object):

    def test_none(self):
        d = configuration.config_parser_to_dict(None)
        assert {} == d

    def test_empty(self):
        d = configuration.config_parser_to_dict(ConfigParser.ConfigParser())
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
        assert d == configuration.config_parser_to_dict(c)
