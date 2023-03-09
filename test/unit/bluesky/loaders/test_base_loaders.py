"""Unit tests for base loaders defined in bluesky.loaders package
"""

import datetime
import os
import tempfile

from py.test import raises

from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)
from bluesky.loaders import BaseJsonFileLoader, BaseCsvFileLoader

class TestBaseFileLoader():

    def setup(self):
        self._temp_dir = tempfile.mkdtemp()

    def test_file_not_defined(self):
        filename = os.path.join(self._temp_dir, "fires.json")

        with raises(BlueSkyConfigurationError) as e_info:
            l = BaseJsonFileLoader()
        assert e_info.value.args[0] == 'Fires file to load not specified'.format(filename)

        with raises(BlueSkyConfigurationError) as e_info:
            l = BaseCsvFileLoader()
        assert e_info.value.args[0] == 'Fires file to load not specified'.format(filename)

    def test_file_doesnt_exist(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with raises(BlueSkyUnavailableResourceError) as e_info:
            l = BaseJsonFileLoader(file=filename)
        assert e_info.value.args[0] == 'Fires file to load {} does not exist'.format(filename)

        with raises(BlueSkyUnavailableResourceError) as e_info:
            l = BaseJsonFileLoader(file=filename)
        assert e_info.value.args[0] == 'Fires file to load {} does not exist'.format(filename)

    def test_file_exists(self):
        filename = os.path.join(self._temp_dir, "fires.json")

        with open(filename, 'w') as f:
            f.write('{}')
        l = BaseJsonFileLoader(file=filename)
        assert l._filename == filename

        with open(filename, 'w') as f:
            f.write('a,b,c')
        l = BaseCsvFileLoader(file=filename)
        assert l._filename == filename

    def test_events_file_doesnt_exist(self):
        pass

    def test_fires_and_events_files_exist(self):
        pass
