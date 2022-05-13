"""Unit tests for bluesky.growers.persistence"""

__author__ = "Joel Dubowy"

import copy
import datetime

from freezegun import freeze_time
from py.test import raises

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.growers import persistence
from bluesky.models.fires import Fire

# TODO: moke Fire class
# TODO: MockFiresManager was copied from test_datautils.py.
#   Move it to common module

class MockFiresManager(object):
    def __init__(self, fires):
        self.fires = [Fire(f) for f in fires]
        self.today = datetime.datetime.now()

    @property
    def fire_failure_handler(self):
        class klass(object):
            def __init__(self, fire):
                pass

            def __enter__(self):
                pass

            def __exit__(self, e_type, value, tb):
                pass

        return klass

    def summarize(self, **summary):
        self.summary = summary


# Note: location data is not relavent to persistence,
#    so keeping it simple
FIRE = {
    "id": "abc123",
    "fuel_type": "natural",
    "type": "wildfire",
    "activity": [
        # 2016-8-1
        {
            "active_areas": [
                {
                    "specified_points": [
                        {'lat': 40, 'lng':-115, 'area': 20,"utc_offset": "-05:00"}
                    ],
                    "start": datetime.datetime(2016,8,1,9,0,0),
                    "end": datetime.datetime(2016,8,1,10,0,0)
                },
                {
                    "specified_points": [
                        {'lat': 40, 'lng':-116, 'area': 40,"utc_offset": "-05:00"}
                    ],
                    "start": datetime.datetime(2016,8,1,13,0,0),
                    # ends at midnight of date to persist, so no
                    # activity on that date
                    "end": datetime.datetime(2016,8,2,0,0,0)
                }
            ]
        },
        # 2016-8-2
        {
            "active_areas": [
                {
                    "specified_points": [
                        {
                            'lat': 41, 'lng':-115,
                            'area': 122,
                            "utc_offset": "-05:00",
                            "timeprofile": {
                                datetime.datetime(2016,8,2,1,0,0): "sdf"
                            },
                            "hourly_frp": {
                                datetime.datetime(2016,8,2,1,0,0): 55.23
                            }
                        }
                    ],
                    "start": datetime.datetime(2016,8,2,1,0,0),
                    "end": datetime.datetime(2016,8,2,3,0,0)
                }
            ]
        },
        # 2016-8-3
        {
            "active_areas": [
                {
                    "specified_points": [
                        {'lat': 41, 'lng':-116, 'area': 323,"utc_offset": "-05:00"}
                    ],
                    "start": datetime.datetime(2016,8,3,13,0,0),
                    "end": datetime.datetime(2016,8,3,18,0,0)
                }
            ]
        },
        # 2016-8-4
        {
            "active_areas": [
                {
                    "specified_points": [
                        {'lat': 41, 'lng':-117, 'area': 54,"utc_offset": "-05:00"}
                    ],
                    "start": datetime.datetime(2016,8,4,1,0,0),
                    "end": datetime.datetime(2016,8,4,8,0,0)
                },
                {
                    "specified_points": [
                        {
                            'lat': 42, 'lng':-117,
                            'area': 66,
                            "utc_offset": "-05:00",
                            "timeprofile": {
                                datetime.datetime(2016,8,4,12,0,0): "zzz"
                            },
                            "hourly_frp": {
                                datetime.datetime(2016,8,4,12,0,0): 10.1
                            }
                        }
                    ],
                    "start": datetime.datetime(2016,8,4,10,0,0),
                    "end": datetime.datetime(2016,8,4,18,0,0)
                }
            ]
        },
        # 2016-8-5 (no activity)
        # 2016-8-6
        {
            "active_areas": [
                {
                    "specified_points": [
                        {'lat': 43, 'lng':-117, 'area': 34,"utc_offset": "-05:00"}
                    ],
                    "start": datetime.datetime(2016,8,6,2,0,0),
                    "end": datetime.datetime(2016,8,6,7,0,0)
                },
                {
                    "specified_points": [
                        {'lat': 42, 'lng':-118, 'area': 253,"utc_offset": "-05:00"}
                    ],
                    "start": datetime.datetime(2016,8,6,15,0,0),
                    "end": datetime.datetime(2016,8,6,19,0,0)
                }
            ]
        }
    ]
}
FIRE_RX = copy.deepcopy(FIRE)
FIRE_RX['type'] = 'rx'


class TestPersistenceInvalidCases(object):

    def test_invalid_calls_string_val_days_to_persist(self, reset_config):
        # days_to_persist isn't an integer
        Config().set({
            "date_to_persist": datetime.datetime(2016,8,1,0,0,0),
            "days_to_persist": 'sdf'
        }, "growth", "persistence")
        with raises(ValueError) as e_info:
            persistence.Grower(MockFiresManager([]))
        assert e_info.value.args[0] == "invalid literal for int() with base 10: 'sdf'"

    def test_invalid_calls_neg_int_val_days_to_persist(self, reset_config):
        # days_to_persist is a negative integer
        Config().set({
            "date_to_persist": datetime.datetime(2016,8,1,0,0,0),
            "days_to_persist": -1
        }, "growth", "persistence")
        with raises(ValueError) as e_info:
            persistence.Grower(MockFiresManager([]))
        assert e_info.value.args[0] == persistence.DAYS_TO_PERSIST_NOT_POS_INT

    def test_invalid_calls_zero_val_days_to_persist(self, reset_config):
        Config().set({
            "date_to_persist": datetime.datetime(2016,8,1,0,0,0),
            "days_to_persist": 0
        }, "growth", "persistence")
        # days_to_persist == 0
        with raises(ValueError) as e_info:
            persistence.Grower(MockFiresManager([]))
        assert e_info.value.args[0] == persistence.DAYS_TO_PERSIST_NOT_POS_INT

    def test_invalid_calls_daily_percentages_not_array(self, reset_config):
        Config().set({
            "date_to_persist": datetime.datetime(2016,8,1,0,0,0),
            "daily_percentages": "asd"
        }, "growth", "persistence")
        # days_to_persist == 0
        with raises(ValueError) as e_info:
            persistence.Grower(MockFiresManager([]))
        assert e_info.value.args[0] == persistence.INVALID_DAILY_PERCENTAGES

    def test_invalid_calls_daily_percentages_and_days_to_persist_both_specified(self, reset_config):
        Config().set({
            "date_to_persist": datetime.datetime(2016,8,1,0,0,0),
            "days_to_persist": 1,
            "daily_percentages": [100]

        }, "growth", "persistence")
        # days_to_persist == 0
        with raises(ValueError) as e_info:
            persistence.Grower(MockFiresManager([]))
        assert e_info.value.args[0] == persistence.DAYS_TO_PERSIST_AND_PERCENTAGES_BOTH_SPECIFIED


class TestPersistencePickCorrectMatchingConfig(object):

    ##
    ## One Config
    ##

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_one_config_date_to_persist_today_no_start_end_days(self, reset_config):
        Config().set([
            {
                "days_to_persist": 2,
                "truncate": True
            },
        ], "growth", "persistence")

        grower = persistence.Grower(MockFiresManager([]))
        assert grower._date_to_persist == datetime.date(2016, 4, 20)
        assert grower._days_to_persist == 2
        assert grower._truncate == True
        assert grower._daily_percentages == [100, 100]

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_one_config_date_to_persist_today_w_start_not_a_match(self, reset_config):
        Config().set([
            {
                "start_day": "05-01",
                "days_to_persist": 2,
                "truncate": True
            },
        ], "growth", "persistence")

        grower = persistence.Grower(MockFiresManager([]))
        assert grower._date_to_persist == None
        assert grower._days_to_persist == 1
        assert grower._truncate == False
        assert grower._daily_percentages == [100]

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_one_config_date_to_persist_set_w_start_and_end_a_match(self, reset_config):
        Config().set([
            {
                "start_day": "05-01",
                "end_day": "10-31",
                "date_to_persist": "2016-10-01",
                "days_to_persist": 2,
                "truncate": True
            },
        ], "growth", "persistence")

        grower = persistence.Grower(MockFiresManager([]))
        assert grower._date_to_persist == datetime.date(2016, 10, 1)
        assert grower._days_to_persist == 2
        assert grower._truncate == True
        assert grower._daily_percentages == [100, 100]

    ##
    ## Multiple Configs
    ##

    @freeze_time("2016-04-20 12:00:00", tz_offset=0)
    def test_two_configs_date_to_persist_today_no_start_end_days(self, reset_config):
        Config().set([
            {
                "days_to_persist": 2,
                "truncate": True
            },
            {
                "days_to_persist": 4,
                "truncate": False
            },
        ], "growth", "persistence")

        grower = persistence.Grower(MockFiresManager([]))
        assert grower._date_to_persist == datetime.date(2016, 4, 20)
        assert grower._days_to_persist == 2
        assert grower._truncate == True
        assert grower._daily_percentages == [100, 100]


    @freeze_time("2016-08-20 12:00:00", tz_offset=0)
    def test_five_configs_date_to_persist_today_start_end_days(self, reset_config):
        Config().set([
            {
                "end_day": "05-01", # ends before today
                "days_to_persist": 2,
                "truncate": True
            },
            {
                "start_day": "October 01", # starts after today
                "daily_percentages": [100, 50, 50],
                "truncate": True
            },
            {
                "start_day": "06-01",
                "end_day": "Jun 30", # ends before today
                "days_to_persist": 4,
                "truncate": True
            },
            {
                "start_day": "07-01",  # This is a match
                "daily_percentages": [100, 50, 50, 25, 25],
                "truncate": False
            },
            {
                "end_day": "11-01",  # This is also a match, but not picked
                "days_to_persist": 6,
                "truncate": False
            },

        ], "growth", "persistence")

        grower = persistence.Grower(MockFiresManager([]))
        assert grower._date_to_persist == datetime.date(2016, 8, 20)
        assert grower._days_to_persist == 5
        assert grower._truncate == False
        assert grower._daily_percentages == [100, 50, 50, 25, 25]


class TestPersistenceEmptyCases(object):

    def setup(self):
        Config().set({
            "date_to_persist": datetime.date(2016,8,6),
            "days_to_persist": 1,
        }, "growth", "persistence")

    def test_no_fires(self, reset_config):
        fm = MockFiresManager([])
        persistence.Grower(fm).grow()
        assert fm.fires == []

    def test_no_activity(self, reset_config):
        fm = MockFiresManager([{"id": 'abc123'}])
        persistence.Grower(fm).grow()
        assert fm.fires == [{"id": 'abc123', 'type': 'wildfire', 'fuel_type': 'natural'}]

    def test_empty_activity(self, reset_config):
        fm = MockFiresManager([{"id": 'abc123', 'activity': []}])
        persistence.Grower(fm).grow()
        assert fm.fires == [{"id": 'abc123', 'type': 'wildfire', 'fuel_type': 'natural', 'activity': []}]


class TestPersistenceRx(object):
    """For prescribed burns, presistence does nothing (i.e. it returns
    activity data identical to the raw data)
    """

    def test_persist_2016_8_7(self, reset_config):
        """All activity before day to persist
        """
        expected = copy.deepcopy(FIRE_RX)
        dates = [
            datetime.datetime(2016,8,7),
            datetime.datetime(2016,8,6),
            datetime.datetime(2016,8,5),
            datetime.datetime(2016,8,4),
            datetime.datetime(2016,8,3),
            datetime.datetime(2016,8,2),
            datetime.datetime(2016,8,1),
            datetime.datetime(2016,7,31)
        ]
        for date_to_persist in dates:
            for truncate in (True, False):
                for days_to_persist in (1,2,3):
                    Config().set({
                        'date_to_persist': date_to_persist,
                        'days_to_persist': days_to_persist,
                        'truncate': truncate
                    }, "growth", "persistence")

                    fire = copy.deepcopy(FIRE_RX)
                    fm = MockFiresManager([fire])
                    persistence.Grower(fm).grow()
                    assert fm.fires == [expected]

class TestPersistenceWfWithTruncation(object):

    def setup(self):
        Config().set({
            # 'date_to_persist' will be changed by each test
            "date_to_persist": datetime.date(2016,8,7),
            "days_to_persist": 2,
            'truncate': True,
        }, "growth", "persistence")


    def test_persist_2016_8_7(self, reset_config):
        """All activity before day to persist

        There's nothing to persist, regardless of config settings
        """
        Config().set(datetime.date(2016,8,7),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]


    def test_persist_2016_8_6(self, reset_config):
        """Activity before and on day to persist
        """
        Config().set(datetime.date(2016,8,6),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        expected['activity'].extend([
            # 2016-8-7
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 43, 'lng':-117, 'area': 34,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,7,2,0,0),
                        "end": datetime.datetime(2016,8,7,7,0,0)
                    },
                    {
                        "specified_points": [
                            {'lat': 42, 'lng':-118, 'area': 253,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,7,15,0,0),
                        "end": datetime.datetime(2016,8,7,19,0,0)
                    }
                ]
            },
            # 2016-8-8
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 43, 'lng':-117, 'area': 34,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,8,2,0,0),
                        "end": datetime.datetime(2016,8,8,7,0,0)
                    },
                    {
                        "specified_points": [
                            {'lat': 42, 'lng':-118, 'area': 253,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,8,15,0,0),
                        "end": datetime.datetime(2016,8,8,19,0,0)
                    }
                ]
            }
        ])

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_5(self, reset_config):
        """Activity before and after, but not on day to persist
        """
        Config().set(datetime.date(2016,8,5),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        expected['activity'].pop() # 8/6 gets truncated

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_4(self, reset_config):
        """Growth before, on, and after day to persist
        """
        Config().set(datetime.date(2016,8,4),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        # 8/6 gets truncated, and then 8/5 and 8/6 get added
        expected['activity'].pop()
        expected['activity'].extend([
            # 2016-8-5
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 41, 'lng':-117, 'area': 54,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,5,1,0,0),
                        "end": datetime.datetime(2016,8,5,8,0,0)
                    },
                    {
                        "specified_points": [
                            {
                                'lat': 42, 'lng':-117,
                                'area': 66,
                                "utc_offset": "-05:00",
                                "timeprofile": {
                                    datetime.datetime(2016,8,5,12,0,0): "zzz"
                                },
                                "hourly_frp": {
                                    datetime.datetime(2016,8,5,12,0,0): 10.1
                                }
                            }
                        ],
                        "start": datetime.datetime(2016,8,5,10,0,0),
                        "end": datetime.datetime(2016,8,5,18,0,0)
                    }
                ]
            },
            # 2016-8-6
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 41, 'lng':-117, 'area': 54,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,6,1,0,0),
                        "end": datetime.datetime(2016,8,6,8,0,0)
                    },
                    {
                        "specified_points": [
                            {
                                'lat': 42, 'lng':-117,
                                'area': 66,
                                "utc_offset": "-05:00",
                                "timeprofile": {
                                    datetime.datetime(2016,8,6,12,0,0): "zzz"
                                },
                                "hourly_frp": {
                                    datetime.datetime(2016,8,6,12,0,0): 10.1
                                }
                            }
                        ],
                        "start": datetime.datetime(2016,8,6,10,0,0),
                        "end": datetime.datetime(2016,8,6,18,0,0)
                    }
                ]
            }
        ])

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_3(self, reset_config):
        """Growth before, on, and after day to persist
        """
        Config().set(datetime.date(2016,8,3),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        # 8/6 and 8/4 get truncated (there is no 8/5), and then
        # 8/4 and 8/5 get added
        expected['activity'].pop()
        expected['activity'].pop()
        expected['activity'].extend([
            # 2016-8-4
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 41, 'lng':-116, 'area': 323,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,4,13,0,0),
                        "end": datetime.datetime(2016,8,4,18,0,0)
                    }
                ]
            },
            # 2016-8-5
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 41, 'lng':-116, 'area': 323,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,5,13,0,0),
                        "end": datetime.datetime(2016,8,5,18,0,0)
                    }
                ]
            }
        ])

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_2(self, reset_config):
        """Growth before, on, and after day to persist
        """
        Config().set(datetime.date(2016,8,2),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        # 8/6, 8/4, 8/3 get truncated (there is no 8/5), and then
        # 8/3 and 8/4 get added
        expected['activity'].pop()
        expected['activity'].pop()
        expected['activity'].pop()
        expected['activity'].extend([
            # 2016-8-3
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {
                                'lat': 41, 'lng':-115,
                                'area': 122,
                                "utc_offset": "-05:00",
                                "timeprofile": {
                                    datetime.datetime(2016,8,3,1,0,0): "sdf"
                                },
                                "hourly_frp": {
                                    datetime.datetime(2016,8,3,1,0,0): 55.23
                                }
                            }
                        ],
                        "start": datetime.datetime(2016,8,3,1,0,0),
                        "end": datetime.datetime(2016,8,3,3,0,0)
                    }
                ]
            },
            # 2016-8-4
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {
                                'lat': 41, 'lng':-115,
                                'area': 122,
                                "utc_offset": "-05:00",
                                "timeprofile": {
                                    datetime.datetime(2016,8,4,1,0,0): "sdf"
                                },
                                "hourly_frp": {
                                    datetime.datetime(2016,8,4,1,0,0): 55.23
                                }
                            }
                        ],
                        "start": datetime.datetime(2016,8,4,1,0,0),
                        "end": datetime.datetime(2016,8,4,3,0,0)
                    }
                ]
            }
        ])

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_1(self, reset_config):
        """Growth on and after day to persist
        """
        Config().set(datetime.date(2016,8,1),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        # 8/6, 8/4, 8/3, 8/2 get truncated (there is no 8/5), and then
        # 8/2 and 8/3 get added
        expected['activity'].pop()
        expected['activity'].pop()
        expected['activity'].pop()
        expected['activity'].pop()
        expected['activity'].extend([
            # 2016-8-2
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 40, 'lng':-115, 'area': 20,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,2,9,0,0),
                        "end": datetime.datetime(2016,8,2,10,0,0)
                    },
                    {
                        "specified_points": [
                            {'lat': 40, 'lng':-116, 'area': 40,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,2,13,0,0),
                        # ends at midnight of date to persist, so no
                        # growth on that date
                        "end": datetime.datetime(2016,8,3,0,0,0)
                    }
                ]
            },
            # 2016-8-3
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 40, 'lng':-115, 'area': 20,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,3,9,0,0),
                        "end": datetime.datetime(2016,8,3,10,0,0)
                    },
                    {
                        "specified_points": [
                            {'lat': 40, 'lng':-116, 'area': 40,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,3,13,0,0),
                        # ends at midnight of date to persist, so no
                        # growth on that date
                        "end": datetime.datetime(2016,8,4,0,0,0)
                    }
                ]
            },
        ])

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_7_31(self, reset_config):
        """All growth after day to persist
        """
        Config().set(datetime.date(2016,7,31),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        expected['activity'] = []

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]


class TestPersistenceWfWithoutTruncation(object):

    def setup(self):
        Config().set({
            # 'date_to_persist' will be changed by each test
            "date_to_persist": datetime.date(2016,8,7),
            "days_to_persist": 2,
            'truncate': False,
        }, "growth", "persistence")


    def test_persist_2016_8_7(self, reset_config):
        """All activity before day to persist

        There's nothing to persist, regardless of config settings
        """
        Config().set(datetime.date(2016,8,7),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_6(self, reset_config):
        """Activity before and on day to persist
        """
        Config().set(datetime.date(2016,8,6),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)
        expected['activity'].extend([
            # 2016-8-7
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 43, 'lng':-117, 'area': 34,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,7,2,0,0),
                        "end": datetime.datetime(2016,8,7,7,0,0)
                    },
                    {
                        "specified_points": [
                            {'lat': 42, 'lng':-118, 'area': 253,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,7,15,0,0),
                        "end": datetime.datetime(2016,8,7,19,0,0)
                    }
                ]
            },
            # 2016-8-8
            {
                "persisted": True,
                "active_areas": [
                    {
                        "specified_points": [
                            {'lat': 43, 'lng':-117, 'area': 34,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,8,2,0,0),
                        "end": datetime.datetime(2016,8,8,7,0,0)
                    },
                    {
                        "specified_points": [
                            {'lat': 42, 'lng':-118, 'area': 253,"utc_offset": "-05:00"}
                        ],
                        "start": datetime.datetime(2016,8,8,15,0,0),
                        "end": datetime.datetime(2016,8,8,19,0,0)
                    }
                ]
            }
        ])

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_5(self, reset_config):
        """Growth before and after, but not on day to persist
        """
        Config().set(datetime.date(2016,8,5),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]


    def test_persist_2016_8_4(self, reset_config):
        """Growth before, on, and after day to persist
        """
        Config().set(datetime.date(2016,8,4),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_3(self, reset_config):
        """Growth before, on, and after day to persist
        """
        Config().set(datetime.date(2016,8,3),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_2(self, reset_config):
        """Growth before, on, and after day to persist
        """
        Config().set(datetime.date(2016,8,2),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_8_1(self, reset_config):
        """Growth on and after day to persist
        """
        Config().set(datetime.date(2016,8,1),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]

    def test_persist_2016_7_31(self, reset_config):
        """All growth after day to persist
        """
        Config().set(datetime.date(2016,7,31),
            "growth", "persistence", "date_to_persist")

        expected = copy.deepcopy(FIRE)

        fire = copy.deepcopy(FIRE)
        fm = MockFiresManager([fire])
        persistence.Grower(fm).grow()
        assert fm.fires == [expected]


class TestPersistenceWfWtihDailyPercentages(object):

    def test(self, reset_config):
        Config().set({
            "date_to_persist": datetime.date(2016,8,1),
            "daily_percentages": [100, 50],
            'truncate': True,
        }, "growth", "persistence")

        fm = MockFiresManager([{
            "id": "abc123",
            "fuel_type": "natural",
            "type": "wildfire",
            "activity": [
                # 2016-8-1
                {
                    "active_areas": [
                        {
                            "start": datetime.datetime(2016,8,1,8,0,0),
                            "end": datetime.datetime(2016,8,1,10,0,0),
                            "consumption": {"summary": {"flaming": 100,"residual": 80,"smoldering": 40,"total": 220}},
                            "dropout": True,
                            "emissions": {"summary": {"PM10": 20,"PM2.5": 10,"total": 30}},
                            "heat": {"summary": {"flaming": 400,"residual": 200,"smoldering": 100,"total": 700}},
                            "specified_points": [
                                {
                                    'lat': 40,'lng':-115,'area': 20,"utc_offset": "-05:00",
                                    "consumption": {"summary": {"flaming": 100,"residual": 80,"smoldering": 40,"total": 220}},
                                    "dropout": True,
                                    "emissions": {"summary": {"PM10": 20,"PM2.5": 10,"total": 30}},
                                    "heat": {"summary": {"flaming": 400,"residual": 200,"smoldering": 100,"total": 700}},
                                    "frp": 20,
                                    "fuelmoisture": {
                                        "2016-08-01T08:00:00": {"1000_hr": 15,"100_hr": 9},
                                        "2016-08-01T09:00:00": {"1000_hr": 15,"100_hr": 9},
                                    },
                                    "fuelbeds": [
                                        {
                                            "fccs_id": "52", "pct": 100.0,
                                            "consumption": {
                                                "canopy": {
                                                    "ladder fuels": {"flaming": [80],"residual": [60],"smoldering": [30]},
                                                    "midstory": {"flaming": [20],"residual": [20],"smoldering": [10]}
                                                }
                                            },
                                            "emissions": {
                                                "flaming": {"PM10": [16],"PM2.5": [8],"total": [20]},
                                                "residual": {"PM10": [4],"PM2.5": [2],"total": [10]},
                                                "smoldering": {"PM10": [0],"PM2.5": [0],"total": [0]},
                                                "total": {"PM10": [20],"PM2.5": [10],"total": [30]}
                                            },
                                            "heat": {"flaming": [400],"residual": [200],"smoldering": [100],"total": [700]}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }])

        expected = [{
            "id": "abc123",
            "fuel_type": "natural",
            "type": "wildfire",
            "activity": [
                # 2016-8-1
                {
                    "active_areas": [
                        {
                            "start": datetime.datetime(2016,8,1,8,0,0),
                            "end": datetime.datetime(2016,8,1,10,0,0),
                            "consumption": {"summary": {"flaming": 100,"residual": 80,"smoldering": 40,"total": 220}},
                            "dropout": True,
                            "emissions": {"summary": {"PM10": 20,"PM2.5": 10,"total": 30}},
                            "heat": {"summary": {"flaming": 400,"residual": 200,"smoldering": 100,"total": 700}},
                            "specified_points": [
                                {
                                    'lat': 40,'lng':-115,'area': 20,"utc_offset": "-05:00",
                                    "consumption": {"summary": {"flaming": 100,"residual": 80,"smoldering": 40,"total": 220}},
                                    "dropout": True,
                                    "emissions": {"summary": {"PM10": 20,"PM2.5": 10,"total": 30}},
                                    "heat": {"summary": {"flaming": 400,"residual": 200,"smoldering": 100,"total": 700}},
                                    "frp": 20,
                                    "fuelmoisture": {
                                        "2016-08-01T08:00:00": {"1000_hr": 15,"100_hr": 9},
                                        "2016-08-01T09:00:00": {"1000_hr": 15,"100_hr": 9},
                                    },
                                    "fuelbeds": [
                                        {
                                            "fccs_id": "52", "pct": 100.0,
                                            "consumption": {
                                                "canopy": {
                                                    "ladder fuels": {"flaming": [80],"residual": [60],"smoldering": [30]},
                                                    "midstory": {"flaming": [20],"residual": [20],"smoldering": [10]}
                                                }
                                            },
                                            "emissions": {
                                                "flaming": {"PM10": [16],"PM2.5": [8],"total": [20]},
                                                "residual": {"PM10": [4],"PM2.5": [2],"total": [10]},
                                                "smoldering": {"PM10": [0],"PM2.5": [0],"total": [0]},
                                                "total": {"PM10": [20],"PM2.5": [10],"total": [30]}
                                            },
                                            "heat": {"flaming": [400],"residual": [200],"smoldering": [100],"total": [700]}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                # 2016-8-2  -  100%
                {
                    "persisted": True,
                    "active_areas": [
                        {
                            "start": datetime.datetime(2016,8,2,8,0,0),
                            "end": datetime.datetime(2016,8,2,10,0,0),
                            "consumption": {"summary": {"flaming": 100,"residual": 80,"smoldering": 40,"total": 220}},
                            "dropout": True,
                            "emissions": {"summary": {"PM10": 20,"PM2.5": 10,"total": 30}},
                            "heat": {"summary": {"flaming": 400,"residual": 200,"smoldering": 100,"total": 700}},
                            "specified_points": [
                                {
                                    'lat': 40,'lng':-115,'area': 20,"utc_offset": "-05:00",
                                    "consumption": {"summary": {"flaming": 100,"residual": 80,"smoldering": 40,"total": 220}},
                                    "dropout": True,
                                    "emissions": {"summary": {"PM10": 20,"PM2.5": 10,"total": 30}},
                                    "heat": {"summary": {"flaming": 400,"residual": 200,"smoldering": 100,"total": 700}},
                                    "frp": 20,
                                    "fuelmoisture": {
                                        "2016-08-01T08:00:00": {"1000_hr": 15,"100_hr": 9},
                                        "2016-08-01T09:00:00": {"1000_hr": 15,"100_hr": 9},
                                    },
                                    "fuelbeds": [
                                        {
                                            "fccs_id": "52", "pct": 100.0,
                                            "consumption": {
                                                "canopy": {
                                                    "ladder fuels": {"flaming": [80],"residual": [60],"smoldering": [30]},
                                                    "midstory": {"flaming": [20],"residual": [20],"smoldering": [10]}
                                                }
                                            },
                                            "emissions": {
                                                "flaming": {"PM10": [16],"PM2.5": [8],"total": [20]},
                                                "residual": {"PM10": [4],"PM2.5": [2],"total": [10]},
                                                "smoldering": {"PM10": [0],"PM2.5": [0],"total": [0]},
                                                "total": {"PM10": [20],"PM2.5": [10],"total": [30]}
                                            },
                                            "heat": {"flaming": [400],"residual": [200],"smoldering": [100],"total": [700]}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                # 2016-8-3  -  50%
                {
                    "persisted": True,
                    "active_areas": [
                        {
                            "start": datetime.datetime(2016,8,3,8,0,0),
                            "end": datetime.datetime(2016,8,3,10,0,0),
                            "consumption": {"summary": {"flaming": 50,"residual": 40,"smoldering": 20,"total": 110}},
                            "dropout": True,
                            "emissions": {"summary": {"PM10": 10,"PM2.5": 5,"total": 15}},
                            "heat": {"summary": {"flaming": 200,"residual": 100,"smoldering": 50,"total": 350}},
                            "specified_points": [
                                {
                                    'lat': 40,'lng':-115,'area': 10,"utc_offset": "-05:00",  # STAYS THE SAME
                                    "consumption": {"summary": {"flaming": 50,"residual": 40,"smoldering": 20,"total": 110}},
                                    "dropout": True,
                                    "emissions": {"summary": {"PM10": 10,"PM2.5": 5,"total": 15}},
                                    "heat": {"summary": {"flaming": 200,"residual": 100,"smoldering": 50,"total": 350}},
                                    "frp": 10,
                                    "fuelmoisture": {
                                        "2016-08-01T08:00:00": {"1000_hr": 15,"100_hr": 9},  # STAYS THE SAME
                                        "2016-08-01T09:00:00": {"1000_hr": 15,"100_hr": 9},  # STAYS THE SAME
                                    },
                                    "fuelbeds": [
                                        {
                                            "fccs_id": "52", "pct": 100.0,  # STAYS THE SAME
                                            "consumption": {
                                                "canopy": {
                                                    "ladder fuels": {"flaming": [40],"residual": [30],"smoldering": [15]},
                                                    "midstory": {"flaming": [10],"residual": [10],"smoldering": [5]}
                                                }
                                            },
                                            "emissions": {
                                                "flaming": {"PM10": [8],"PM2.5": [4],"total": [10]},
                                                "residual": {"PM10": [2],"PM2.5": [1],"total": [5]},
                                                "smoldering": {"PM10": [0],"PM2.5": [0],"total": [0]},
                                                "total": {"PM10": [10],"PM2.5": [5],"total": [15]}
                                            },
                                            "heat": {"flaming": [200],"residual": [100],"smoldering": [50],"total": [350]}
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }]

        grower = persistence.Grower(fm)
        grower.grow()
        assert len(fm.fires[0]['activity']) == 3
        assert fm.fires[0]['activity'][0] == expected[0]['activity'][0]
        assert fm.fires[0]['activity'][1] == expected[0]['activity'][1]
        assert fm.fires[0]['activity'][2] == expected[0]['activity'][2]
        assert fm.fires == expected
