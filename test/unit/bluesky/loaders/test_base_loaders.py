"""Unit tests for base loaders defined in bluesky.loaders package
"""

import datetime
import os
import tempfile

from freezegun import freeze_time
from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.loaders import BaseLoader, BaseFileLoader

# Note: the setting of BaseFileLoader._date_time is tested by
#   test_datetimeutils:TeetToDatetime (since the code is all in
#   datetimeutils.to_datetime)

class TestBaseLoader(object):

    @freeze_time("2016-01-14")
    def test(self):
        l = BaseLoader()
        l._date_time = datetime.date(2016, 1, 14)
        l = BaseLoader(date_time=datetime.date(2016, 2, 14))
        l._date_time = datetime.date(2016, 2, 14)
        l = BaseLoader(date_time=datetime.datetime(2016, 2, 14, 12, 1))
        l._date_time = datetime.datetime(2016, 2, 14, 12, 1)

class TestBaseFileLoader(object):

    def setup(self):
        self._temp_dir = tempfile.mkdtemp()

    def test_file_doesnt_exist(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with raises(BlueSkyConfigurationError) as e_info:
            l = BaseFileLoader(file=filename)
        assert e_info.value.message == 'File {} does not exist'.format(filename)

    def test_file_exists(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with open(filename, 'w') as f:
            f.write('{}')
        l = BaseFileLoader(file=filename)
        assert l._filename == filename
        assert l._events_filename == None

    @freeze_time("2016-01-14")
    def test_file_exists_with_datetime_codes(self):
        filename = os.path.join(self._temp_dir, "fires%Y%m%d.json")
        with open(filename, 'w') as f:
            f.write('{}')
        l = BaseFileLoader(file=filename)
        assert l._filename == filename
        assert l._events_filename == None

    @freeze_time("2016-01-14")
    def test_file_exists_with_defined_date_in_name(self):
        config_filename = os.path.join(self._temp_dir, "fires%Y%m%d.json")
        real_filename = os.path.join(self._temp_dir, "fires20160114.json")
        with open(real_filename, 'w') as f:
            f.write('{}')
        l = BaseFileLoader(file=config_filename)
        assert l._filename == real_filename
        assert l._events_filename == None

    @freeze_time("2016-01-14")
    def test_file_exists_with_different_defined_date_in_name(self):
        config_filename = os.path.join(self._temp_dir, "fires%Y%m%d.json")
        interpolated_filename = os.path.join(self._temp_dir, "fires20160114.json")
        real_filename = os.path.join(self._temp_dir, "fires20151214.json")
        with open(real_filename, 'w') as f:
            f.write('{}')
        with raises(BlueSkyConfigurationError) as e_info:
            l = BaseFileLoader(file=config_filename)
        assert e_info.value.message == 'File {} does not exist'.format(interpolated_filename)

    # TODO: test with events file doesn't exist
    # TODO: test with events file does exist
    # TODO: test with events file does exist with datetime codes
    # TODO: test with events file does exist with date in name
    # TODO: test with events file does exist with different date in name
