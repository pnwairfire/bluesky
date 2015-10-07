"""Unit tests for bluesky.datetimeutils"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from py.test import raises

from bluesky.datetimeutils import parse_utc_offset

##
## Tests for parse_datetimes
##

class TestParseDatetime(object):

    pass

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

