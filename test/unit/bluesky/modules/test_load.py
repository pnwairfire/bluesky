"""Unit tests for bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import copy
import os
import tempfile
import time
from unittest import mock

from py.test import raises

from bluesky.exceptions import BlueSkyUnavailableResourceError
from bluesky.loaders import BaseFileLoader
from bluesky.modules import load


##
## Tests for _load_source, with and without wait
##

FILE_SOURCE_W_WAIT_CONFIG = {
    "name": "firespider",
    "format": "JSON",
    "type": "File",
    "file": None, # Filled in by test
    "wait": {
        "strategy": "fixed",
        "time": 1.0,
        "max_attempts": 5
    }
}

class TestFSFileLoadSource(object):

    def setup(self):
        self._temp_dir = tempfile.mkdtemp()
        self._filename = os.path.join(self._temp_dir, "fires.json")
        self._source = copy.deepcopy(FILE_SOURCE_W_WAIT_CONFIG)
        self._source['file'] = self._filename

    def monkeypatch_sleep(self, monkeypatch, add_file_midway=False):
        self.sleepcount = 0
        self.total_sleep = 0.0
        def mock_sleep(seconds):
            self.sleepcount += 1
            self.total_sleep += seconds
            if add_file_midway and self.sleepcount == 2:
                with open(self._filename, 'w') as f:
                    f.write('{"data": []}')

        monkeypatch.setattr(time, 'sleep', mock_sleep)

    def monkeypatch_load(self, monkeypatch):
        self.load_counter = 0
        def mock_load(_self):
            self.load_counter += 1
            return [{}]
        monkeypatch.setattr(BaseFileLoader, 'load', mock_load)

    def test_no_file_no_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)
        self.monkeypatch_load(monkeypatch)
        self._source.pop('wait')

        with raises(BlueSkyUnavailableResourceError) as e_info:
            load._load_source(self._source)

        assert self.load_counter == 0 # load never called
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0


    def test_no_file_with_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)
        self.monkeypatch_load(monkeypatch)

        with raises(BlueSkyUnavailableResourceError) as e_info:
            load._load_source(self._source)

        assert self.load_counter == 0 # load never called
        assert self.sleepcount == 4
        assert self.total_sleep == 4.0

    def test_no_file_with_backoff_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)
        self.monkeypatch_load(monkeypatch)
        self._source['wait']['strategy'] = 'backoff'

        with raises(BlueSkyUnavailableResourceError) as e_info:
            load._load_source(self._source)

        assert self.load_counter == 0 # load never called
        assert self.sleepcount == 4
        assert self.total_sleep == 15.0

    def test_no_file_initially_with_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch, add_file_midway=True)
        self.monkeypatch_load(monkeypatch)

        load._load_source(self._source)

        assert self.load_counter == 1
        assert self.sleepcount == 2
        assert self.total_sleep == 2.0

    def test_no_file_initially_with_backoff_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch, add_file_midway=True)
        self.monkeypatch_load(monkeypatch)
        self._source['wait']['strategy'] = 'backoff'

        load._load_source(self._source)

        assert self.load_counter == 1
        assert self.sleepcount == 2
        assert self.total_sleep == 3.0

    def test_file_exists_no_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)
        self.monkeypatch_load(monkeypatch)
        self._source.pop('wait')

        with open(self._filename, 'w') as f:
            f.write('{}')

        load._load_source(self._source)

        assert self.load_counter == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0

    def test_file_exists_with_wait(self, monkeypatch):
        self.monkeypatch_sleep(monkeypatch)
        self.monkeypatch_load(monkeypatch)

        with open(self._filename, 'w') as f:
            f.write('{}')

        load._load_source(self._source)

        assert self.load_counter == 1
        assert self.sleepcount == 0
        assert self.total_sleep == 0.0


class TestFSApiLoadSource(object):
    pass
