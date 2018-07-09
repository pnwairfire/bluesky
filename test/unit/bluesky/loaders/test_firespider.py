"""Unit tests for bluesky.loaders.firespider
"""

import copy
import datetime

from py.test import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.loaders import firespider

FT_FIRES = [
    {
        "id": "HMS_sdfsdfsdf",
        "source": "HMS",
        "name": "HMS_sdfsdfsdf",
        "fuel_type": "natural",
        "type": "wildfire",
        "growth": [
            {
                "start": "2015-08-09T07:00:00Z",
                "end": "2015-08-10T07:00:00Z",
                "timeprofile": {
                    "2015-08-09T07:00:00Z": {
                        'flaming': 0.4118236472945892,
                        'smoldering': 0.4118236472945892,
                        'residual': 0.4118236472945892
                    },
                    "2015-08-09T13:00:00Z":  {
                        'flaming': 0.30661322645290584,
                        'smoldering': 0.30661322645290584,
                        'residual': 0.30661322645290584
                    },
                    "2015-08-10T09:00:00Z": {
                        'flaming': 0.28156312625250507,
                        'smoldering': 0.28156312625250507,
                        'residual': 0.28156312625250507
                    },
                },
                "hourly_frp": {
                    "2015-08-09T07:00:00Z": 47.333333333333336,
                    "2015-08-09T13:00:00Z":  45.0,
                    "2015-08-10T09:00:00Z": 53.166666666666664
                },
                "location": {
                    "area": 900,
                    "geojson": {
                        "type": "MultiPoint",
                        "coordinates": [
                            [-120.2, 48.1],
                            [-120.4, 48.2],
                            [-120.2, 48.2]
                        ]
                    },
                    "utc_offset": "-07:00"
                }
            },
            {
                "start": "2015-08-10T07:00:00Z",
                "end": "2015-08-11T07:00:00Z",
                "location": {
                    "area": 300,
                    "geojson": {
                        "type": "MultiPoint",
                        "coordinates": [[-120.2, 48.1]]
                    },
                    "utc_offset": "-07:00"
                }
            }
        ]
    }
]
MARSHALED = [
    {
        "id": "HMS_sdfsdfsdf",
        "source": "HMS",
        "name": "HMS_sdfsdfsdf",
        "fuel_type": "natural",
        "type": "wildfire",
        "growth": [
            {
                "start": datetime.datetime(2015,8,9,0,0,0),
                "end": datetime.datetime(2015,8,10,0,0,0),
                "timeprofile": {
                    "2015-08-09T00:00:00": {
                        'flaming': 0.4118236472945892,
                        'smoldering': 0.4118236472945892,
                        'residual': 0.4118236472945892
                    },
                    "2015-08-09T06:00:00":  {
                        'flaming': 0.30661322645290584,
                        'smoldering': 0.30661322645290584,
                        'residual': 0.30661322645290584
                    },
                    "2015-08-10T02:00:00": {
                        'flaming': 0.28156312625250507,
                        'smoldering': 0.28156312625250507,
                        'residual': 0.28156312625250507
                    },
                },
                "hourly_frp": {
                    "2015-08-09T00:00:00": 47.333333333333336,
                    "2015-08-09T06:00:00":  45.0,
                    "2015-08-10T02:00:00": 53.166666666666664
                },
                "location": {
                    "area": 900,
                    "geojson": {
                        "type": "MultiPoint",
                        "coordinates": [
                            [-120.2, 48.1],
                            [-120.4, 48.2],
                            [-120.2, 48.2]
                        ]
                    },
                    "utc_offset": "-07:00"
                }
            },
            {
                "start": datetime.datetime(2015,8,10,0,0,0),
                "end": datetime.datetime(2015,8,11,0,0,0),
                "location": {
                    "area": 300,
                    "geojson": {
                        "type": "MultiPoint",
                        "coordinates": [[-120.2, 48.1]]
                    },
                    "utc_offset": "-07:00"
                }
            }
        ]
    }
]

class TestBaseFireSpiderLoader(object):

    def setup(self):
        pass


    ##
    ## _marshal
    ##

    def _call_marshal(self, fires, start=None, end=None):
        loader = firespider.JsonApiLoader(endpoint="sdf",
            start=start, end=end)
        return loader._marshal(fires)

    def test_marshal_no_start_end(self):
        assert MARSHALED == self._call_marshal(
            copy.deepcopy(FT_FIRES))

    def test_marshal_w_start(self):
        expected = copy.deepcopy(MARSHALED)

        # start is before all growth windows
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,8,7,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-08T07:00:00Z")

        # start is in the middle of first growth window
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,9,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-09T14:00:00Z")

        # start is in the middle of second growth window
        expected[0]['growth'].pop(0)
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,10,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-10T14:00:00Z")

        # start is after all growth windows
        expected[0]['growth'].pop(0)
        assert expected[0]['growth'] == [] # for sanity
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,12,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-12T14:00:00Z")

    def test_marshal_w_end(self):
        expected = copy.deepcopy(MARSHALED)

        # end is after all growth windows
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end=datetime.datetime(2015,8,12,7,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end="2015-08-12T07:00:00Z")

        # start is in the middle of second growth window
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end=datetime.datetime(2015,8,10,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end="2015-08-10T14:00:00Z")

        # start is in the middle of first growth window
        expected[0]['growth'].pop()
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end=datetime.datetime(2015,8,9,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end="2015-08-09T14:00:00Z")

        # start is before all growth windows
        expected[0]['growth'].pop()
        assert expected[0]['growth'] == [] # for sanity
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end=datetime.datetime(2015,8,8,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            end="2015-08-08T14:00:00Z")

    def test_marshal_w_start_and_end(self):
        expected = copy.deepcopy(MARSHALED)

        # start/end are outside of growth windows
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,8,7,0,0),
            end=datetime.datetime(2015,8,12,7,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-08T07:00:00Z",
            end="2015-08-12T07:00:00Z")

        # start/end are inside, but including all growth windows
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,9,14,0,0),
            end=datetime.datetime(2015,8,10,14,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-09T14:00:00Z",
            end="2015-08-10T14:00:00Z")

        # start/end are inside first growth window
        expected[0]['growth'].pop()
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,9,14,0,0),
            end=datetime.datetime(2015,8,10,1,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-09T14:00:00Z",
            end="2015-08-10T01:00:00Z")

        # exclude all growth windows
        expected[0]['growth'].pop()
        assert expected[0]['growth'] == [] # for sanity
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start=datetime.datetime(2015,8,7,14,0,0),
            end=datetime.datetime(2015,8,8,1,0,0))
        assert expected == self._call_marshal(
            copy.deepcopy(FT_FIRES),
            start="2015-08-07T14:00:00Z",
            end="2015-08-08T01:00:00Z")


        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FT_FIRES),
                start=datetime.datetime(2015,8,7,14,0,0),
                end=datetime.datetime(2015,8,4,1,0,0))
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG
        with raises(BlueSkyConfigurationError) as e_info:
            self._call_marshal(
                copy.deepcopy(FT_FIRES),
                start="2015-08-07T14:00:00Z",
                end="2015-08-04T01:00:00Z")
        assert e_info.value.args[0] == firespider.BaseFireSpiderLoader.START_AFTER_END_ERROR_MSG


    ##
    ## Helper methods
    ##

    def test_convert_keys_to_local_time(self):
        d = {
            "timeprofile": {
                "2015-08-09T07:00:00Z": {
                    'flaming': 0.4118236472945892,
                    'smoldering': 0.4118236472945892,
                    'residual': 0.4118236472945892
                },
                "2015-08-09T13:00:00Z":  {
                    'flaming': 0.30661322645290584,
                    'smoldering': 0.30661322645290584,
                    'residual': 0.30661322645290584
                },
                "2015-08-10T09:00:00Z": {
                    'flaming': 0.28156312625250507,
                    'smoldering': 0.28156312625250507,
                    'residual': 0.28156312625250507
                },
            },
            "hourly_frp": {
                "2015-08-09T07:00:00Z": 47.333333333333336,
                "2015-08-09T13:00:00Z":  45.0,
                "2015-08-10T09:00:00Z": 53.166666666666664
            }
        }
        expected = {
            "timeprofile": {
                "2015-08-09T03:00:00": {
                    'flaming': 0.4118236472945892,
                    'smoldering': 0.4118236472945892,
                    'residual': 0.4118236472945892
                },
                "2015-08-09T09:00:00":  {
                    'flaming': 0.30661322645290584,
                    'smoldering': 0.30661322645290584,
                    'residual': 0.30661322645290584
                },
                "2015-08-10T05:00:00": {
                    'flaming': 0.28156312625250507,
                    'smoldering': 0.28156312625250507,
                    'residual': 0.28156312625250507
                },
            },
            "hourly_frp": {
                "2015-08-09T00:00:00": 47.333333333333336,
                "2015-08-09T06:00:00":  45.0,
                "2015-08-10T02:00:00": 53.166666666666664
            }
        }

        loader = firespider.JsonApiLoader(endpoint="sdf",
            start=datetime.datetime(2015,8,9,0,0,0),
            end=datetime.datetime(2015,8,11,0,0,0))
        # Note: using different offsets for timeporfile and hourly_frp
        loader._convert_keys_to_local_time(d, 'timeprofile',
            datetime.timedelta(hours=-4))
        loader._convert_keys_to_local_time(d, 'hourly_frp',
            datetime.timedelta(hours=-7))

        # d should have been modified in place
        assert d == expected