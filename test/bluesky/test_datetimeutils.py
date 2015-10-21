"""Unit tests for bluesky.datetimeutils"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
from py.test import raises

from bluesky.datetimeutils import (
    parse_datetime,
    parse_datetimes,
    parse_utc_offset
)

##
## Tests for parse_datetime
##

class TestParseDatetime(object):

    def test_invalid(self):
        with raises(ValueError):
            parse_datetime(None, 'start')
        with raises(ValueError):
            parse_datetime('sdfsdf', 'start')

    def test_valid(self):
        dt = datetime.datetime(2015, 2, 1, 10, 9, 8)
        assert parse_datetime('2015-02-01T10:09:08', 'start') == dt
        # TODO: test other formats

##
## Tests for parse_datetimes
##

class TestParseDatetimes(object):

    def test_invalid(self):
        # Missing key
        with raises(ValueError):
            parse_datetimes({}, 'start')
        with raises(ValueError):
            parse_datetimes({'s': 123}, 'start')
        with raises(ValueError):
            parse_datetimes({'s': '2015-02-01T10:09:08'}, 's', 'e')

        # invalid values
        with raises(ValueError):
            parse_datetimes({'s':None, 'e':'sdfsdf'}, 's')
        with raises(ValueError):
            parse_datetimes({'s':'sdf', 'e':'sdfsdf'}, 's')

    def test_valid(self):
        s = datetime.datetime(2015, 2, 1, 10, 9, 8)
        e = datetime.datetime(2015, 2, 1, 12, 9, 8)
        s_only = {'s': '2015-02-01T10:09:08'}
        e_only = {'e': '2015-02-01T12:09:08'}
        s_and_e = {'s': '2015-02-01T10:09:08', 'e': '2015-02-01T12:09:08'}

        assert parse_datetimes(s_only, 's') == {'s': s}
        assert parse_datetimes(s_and_e, 's') == {'s': s}
        assert parse_datetimes(e_only, 'e') == {'e': e}
        assert parse_datetimes(s_and_e, 'e') == {'e': e}
        assert parse_datetimes(s_and_e, 's', 'e') == {'s': s, 'e': e}

##
## Tests for summarize
##

class TestParseUtcOffset(object):

    def test_invalid(self):
        with raises(ValueError):
            parse_utc_offset(None)
        with raises(ValueError):
            parse_utc_offset('-sfd')
        with raises(ValueError):
            parse_utc_offset('+34:23')
        with raises(ValueError):
            parse_utc_offset('-04:66')

    def test_valid(self):
        assert 0.0 == parse_utc_offset('+00:00')
        assert 4.0 == parse_utc_offset('+04:00')
        assert -3.5 == parse_utc_offset('-03:30')

