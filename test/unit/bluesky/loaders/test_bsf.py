"""Unit tests for bluesky.loaders.firespider
"""

import copy
import datetime
import json
import os

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.loaders import bsf
from bluesky.datetimeutils import parse_datetime

data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


##
## Base test class
##

class TestBsfLoader(object):

    INPUT_FILENAME = os.path.join(data_dir, 'bsf-input.csv')
    LOADED_FILENAME = os.path.join(data_dir, 'bsf-loaded.json')


    def setup(self):
        # with open(FSV2_INPUT_FILENAME) as f:
        #     self._input = json.loads(f.read())
        with open(self.LOADED_FILENAME) as f:
            self._expected_output = json.loads(f.read())
            self._expected_output.sort(key=lambda f: f['id'])
        # convert timestamps to datetime objects
        for f in self._expected_output:
            for a in f.get('activity', []):
                for aa in a.get('active_areas', []):
                    aa['start'] = parse_datetime(aa['start'])
                    aa['end'] = parse_datetime(aa['end'])

    def _call_marshal(self, start=None, end=None):
        loader = bsf.CsvFileLoader(
            file=self.INPUT_FILENAME,
            start=start, end=end)
        actual = loader.load()
        actual.sort(key=lambda f: f['id'])
        assert actual == self._expected_output

    ## With 'start' option

    def test_marshal_no_start_end(self):
        self._call_marshal()

    def test_marshal_w_start_before_all_activity(self):
        self._call_marshal(start=datetime.datetime(2019,5,27,7,0,0))
        self._call_marshal(start="2019-05-27T00:00:00Z")

    def test_marshal_w_start_mid_first_activity_window(self):
        self._call_marshal(start=datetime.datetime(2019,5,28,14,0,0))
        self._call_marshal(start="2019-05-28T14:00:00Z")

    def test_marshal_w_start_mid_second_activity_window(self):
        self._expected_output[0]['activity'].pop(0)
        self._expected_output[1]['activity'].pop(0)
        self._call_marshal(start=datetime.datetime(2019,5,29,14,0,0))
        self._call_marshal(start="2019-05-29T14:00:00Z")

    def test_marshal_w_start_after_all_activity(self):
        self._expected_output = []
        self._call_marshal(start=datetime.datetime(2019,5,31,14,0,0))
        self._call_marshal(start="2019-05-31T14:00:00Z")

    ## With 'end' option

    def test_marshal_w_end_after_all_activity(self):
        self._call_marshal(end=datetime.datetime(2019,5,31,7,0,0))
        self._call_marshal(end="2019-05-31T00:00:00Z")

    def test_marshal_w_end_mid_second_activity_window(self):
        self._call_marshal(end=datetime.datetime(2019,5,29,14,0,0))
        self._call_marshal(end="2019-05-29T14:00:00Z")

    def test_marshal_w_end_mid_first_activity_window(self):
        self._expected_output[0]['activity'].pop()
        self._expected_output[1]['activity'].pop()
        self._call_marshal(end=datetime.datetime(2019,5,28,14,0,0))
        self._call_marshal(end="2019-05-28T14:00:00Z")

    def test_marshal_w_end_before_all_activity(self):
        self._expected_output = []
        self._call_marshal(end=datetime.datetime(2019,5,27,14,0,0))
        self._call_marshal(end="2019-05-27T14:00:00Z")

    ## With 'start' and 'end' otions

    def test_marshal_w_start_and_end_outside_of_all_activity_windows(self):
        self._call_marshal(start=datetime.datetime(2019,5,27,7,0,0),
            end=datetime.datetime(2019,5,31,7,0,0))
        self._call_marshal(start="2019-05-27T00:00:00",
            end="2019-05-31T00:00:00Z")

    def test_marshal_w_start_and_end_outside_of_but_including_all_activity_windows(self):
        self._call_marshal(start=datetime.datetime(2019,5,28,14,0,0),
            end=datetime.datetime(2019,5,29,14,0,0))
        self._call_marshal(start="2019-05-28T14:00:00",
            end="2019-05-29T14:00:00Z")

    def test_marshal_w_start_and_end_inside_first_activity_windows(self):
        self._expected_output[0]['activity'].pop(1)
        self._expected_output[1]['activity'].pop(1)
        self._call_marshal(start=datetime.datetime(2019,5,28,10,0,0),
            end=datetime.datetime(2019,5,28,17,0,0))
        self._call_marshal(start="2019-05-28T20:00:00Z",
            end="2019-05-29T01:00:00Z")

    def test_marshal_w_start_and_end_exclude_all_activity_windows(self):
        # exclude all activity windows
        self._expected_output = []
        self._call_marshal(start=datetime.datetime(2019,5,20,14,0,0),
            end=datetime.datetime(2019,5,27,1,0,0))
        self._call_marshal(start="2019-05-20T14:00:00",
            end="2019-05-27T01:00:00Z")

    def _test_marshal_invalid_start_end(self):
        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FSV2_FIRE_DATA),
                start=datetime.datetime(2019,5,20,14,0,0),
                end=datetime.datetime(2019,5,4,1,0,0))
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FSV2_FIRE_DATA),
                start="2019-05-20T14:00:00",
                end="2019-05-04T01:00:00Z")
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
