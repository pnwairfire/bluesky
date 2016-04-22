"""Unit tests for base loaders defined in bluesky.loaders package
"""

import datetime
import os
import tempfile

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.loaders import BaseFileLoader

class TestBaseFileLoader(object):

    def setup(self):
        self._temp_dir = tempfile.mkdtemp()

    def test_file_not_defined(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with raises(BlueSkyConfigurationError) as e_info:
            l = BaseFileLoader()
        assert e_info.value.message == 'Fires file to load not specified'.format(filename)

    def test_file_doesnt_exist(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with raises(BlueSkyConfigurationError) as e_info:
            l = BaseFileLoader(file=filename)
        assert e_info.value.message == 'Fires file to load {} does not exist'.format(filename)

    def test_file_exists(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with open(filename, 'w') as f:
            f.write('{}')
        l = BaseFileLoader(file=filename)
        assert l._filename == filename
        assert l._events_filename == None

    def test_events_file_doesnt_exist(self):
        pass

    def test_fires_and_events_files_exist(self):
        pass
