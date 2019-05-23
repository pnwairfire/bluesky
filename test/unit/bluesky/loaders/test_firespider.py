"""Unit tests for bluesky.loaders.firespider
"""

import copy
import datetime

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.loaders import firespider


data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
FSV2_INPUT_FILENAME = os.path.join(data_dir, 'fires-spider-v2-input.json')
FSV2_LOADED_FILENAME = os.path.join(data_dir, 'fires-spider-v2-loaded.json')


##
## FireSpider v2
##

class TestFireSpiderLoaderFSV2(object):

    def setup(self):
        with open(FSV2_INPUT_FILENAME) as f:
            self._input = json.loads(f.read())
        with open(FSV2_LOADED_FILENAME) as f:
            self._expected_output = json.loads(f.read())

    def _call_marshal(self, fires, start=None, end=None):
        loader = firespider.JsonApiLoader(endpoint="sdf",
            start=start, end=end)
        actual = loader._marshal(self._input)
        assert actual == self._expected_output

    ## With 'start' option

    def test_marshal_no_start_end(self):
        self._call_marshal(copy.deepcopy(FSV2_FIRE_DATA))

    def test_marshal_w_start_before_all_activity(self):
        self._call_marshal(start=datetime.datetime(2015,8,8,7,0,0))
        self._call_marshal(start="2015-08-08T00:00:00Z")

    def test_marshal_w_start_mid_first_activity_window(self):
        self._call_marshal(start=datetime.datetime(2015,8,9,14,0,0))
        self._call_marshal(start="2015-08-09T14:00:00Z")

    def test_marshal_w_start_mid_second_activity_window(self):
        self._expected_output[1]['activity'].pop(0)
        self._call_marshal(start=datetime.datetime(2015,8,10,14,0,0))
        self._call_marshal(start="2015-08-10T14:00:00Z")

    def test_marshal_w_start_after_all_activity(self):
        self._expected_output.pop(1)
        self._call_marshal(start=datetime.datetime(2015,8,12,14,0,0))
        self._call_marshal(start="2015-08-12T14:00:00Z")

    ## With 'end' option

    def test_marshal_w_end_after_all_activity(self):
        self._call_marshal(end=datetime.datetime(2015,8,12,7,0,0))
        self._call_marshal(end="2015-08-12T00:00:00Z")

    def test_marshal_w_end_mid_second_activity_window(self):
        self._call_marshal(end=datetime.datetime(2015,8,10,14,0,0))
        self._call_marshal(end="2015-08-10T14:00:00Z")

    def test_marshal_w_end_mid_first_activity_window(self):
        self._expected_output[0]['activity'].pop()
        self._call_marshal(end=datetime.datetime(2015,8,9,14,0,0))
        self._call_marshal(end="2015-08-09T14:00:00Z")

    def test_marshal_w_end_before_all_activity(self):
        self._expected_output = []
        self._call_marshal(end=datetime.datetime(2015,8,8,14,0,0))
        self._call_marshal(end="2015-08-08T14:00:00Z")

    ## With 'start' and 'end' otions

    def test_marshal_w_start_and_end_outside_of_all_activity_windows(self):
        self._call_marshal(start=datetime.datetime(2015,8,8,7,0,0),
            end=datetime.datetime(2015,8,12,7,0,0))
        self._call_marshal(start="2015-08-08T00:00:00",
            end="2015-08-12T00:00:00Z")

    def test_marshal_w_start_and_end_outside_of_but_including_all_activity_windows(self):
        self._call_marshal(start=datetime.datetime(2015,8,9,14,0,0),
            end=datetime.datetime(2015,8,10,14,0,0))
        self._call_marshal(start="2015-08-09T14:00:00",
            end="2015-08-10T14:00:00Z")

    def test_marshal_w_start_and_end_inside_first_activity_windows(self):
        self._expected_output[0]['activity'].pop()
        self._call_marshal(start=datetime.datetime(2015,8,9,14,0,0),
            end=datetime.datetime(2015,8,10,1,0,0))
        self._call_marshal(start="2015-08-09T14:00:00",
            end="2015-08-10T01:00:00Z")

    def test_marshal_w_start_and_end_exclude_all_activity_windows(self):
        # exclude all activity windows
        self._expected_output = []
        self._call_marshal(start=datetime.datetime(2015,8,7,14,0,0),
            end=datetime.datetime(2015,8,8,1,0,0))
        self._call_marshal(start="2015-08-07T14:00:00",
            end="2015-08-08T01:00:00Z")

    def _test_marshal_invalid_start_end(self):
        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FSV2_FIRE_DATA),
                start=datetime.datetime(2015,8,7,14,0,0),
                end=datetime.datetime(2015,8,4,1,0,0))
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FSV2_FIRE_DATA),
                start="2015-08-07T14:00:00",
                end="2015-08-04T01:00:00Z")
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
