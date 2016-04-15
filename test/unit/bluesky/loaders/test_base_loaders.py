"""Unit tests for base loaders defined in bluesky.loaders package
"""

import datetime

from freezegun import freeze_time
from py.test import raises

from bluesky.loaders import BaseLoader, BaseFileLoader

class TestBaseLoader(object):

    @freeze_time("2016-01-14")
    def test_date_not_defined(self):
        l = BaseLoader()
        assert l._date_time == datetime.date(2016, 1, 14)

    @freeze_time("2016-01-14")
    def test_date_defined_as_string(self):
        l = BaseLoader(date_time="20151214")
        assert l._date_time == datetime.datetime(2015, 12, 14)

        l = BaseLoader(date_time="2015-12-14T10:02:01")
        assert l._date_time == datetime.datetime(2015, 12, 14, 10, 2, 1)

    @freeze_time("2016-01-14")
    def test_date_defined_as_date(self):
        l = BaseLoader(date_time=datetime.date(2015, 12, 14))
        assert l._date_time == datetime.date(2015, 12, 14)

        l = BaseLoader(date_time=datetime.datetime(2015, 12, 14, 2, 1, 23))
        assert l._date_time == datetime.datetime(2015, 12, 14, 2, 1, 23)


class TestBaseFileLoader(object):

    def test_file_doesnt_exist(self):
        # TODO: make sure exception is raised
        pass

    def test_file_exists(self):
        # TODO: make sure no exception and self._filename is set appropriately
        pass

    def test_file_exists_with_datetime_codes(self):
        # TODO: make sure no exception and self._filename is set appropriately
        pass

    def test_file_exists_with_defined_date_in_name(self):
        # TODO: make sure no exception and self._filename is set appropriately
        pass

    def test_file_exists_with_different_defined_date_in_name(self):
        # TODO: make sure exception is raised
        pass
