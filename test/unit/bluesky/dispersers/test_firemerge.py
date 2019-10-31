import copy
import datetime
import uuid

from bluesky.dispersers import firemerge
from bluesky.models.fires import Fire


##
## PlumeMerge tests
##

CONSUMPTION = {
    "summary": {
        "flaming": 1311.2071801109494,
        "residual": 1449.3962581338644,
        "smoldering": 1267.0712004277434,
        "total": 4027.6746386725567
    }
}
PLUMERISE_HOUR = {
    "emission_fractions": [
        0.01,0.05,0.05,0.05,0.05,0.05,
        0.09,0.09,0.09,0.05,0.05,0.05,
        0.05,0.05,0.05,0.05,0.05,0.05,
        0.01,0.01
    ],
    "heights": [
        141.438826,200.84066925000002,260.2425125,
        319.64435575,379.046199,438.44804225,
        497.84988549999997,557.25172875,616.6535719999999,
        676.0554152499999,735.4572585000001,794.85910175,
        854.260945,913.66278825,973.0646314999999,
        1032.46647475,1091.868318,1151.27016125,
        1210.6720045,1270.0738477500001,1329.475691
    ],
    "smolder_fraction": 0.05
}
EMPTY_PLUMERISE_HOUR = {
    "emission_fractions": [
        0.05,0.05,0.05,0.05,0.05,0.05,
        0.05,0.05,0.05,0.05,0.05,0.05,
        0.05,0.05,0.05,0.05,0.05,0.05,
        0.05,0.05
    ],
    "heights": [
        0.0,0.0,0.0,0.0,0.0,0.0,
        0.0,0.0,0.0,0.0,0.0,0.0,
        0.0,0.0,0.0,0.0,0.0,0.0,
        0.0,0.0,0.0
    ],
    "smolder_fraction": 0.0
}

class TestFireMerger(object):

    FIRE_1 = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'bar'},
        "start": datetime.datetime(2015,8,4,17,0,0),
        "end": datetime.datetime(2015,8,4,19,0,0),
        "area": 120.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T17:00:00": PLUMERISE_HOUR,
            "2015-08-04T18:00:00": EMPTY_PLUMERISE_HOUR
        },
        "timeprofile": {
            "2015-08-04T17:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            },
            "2015-08-04T18:00:00": {
                "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0, 'CO': 2.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T17:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
            "2015-08-04T18:00:00": {"CO": 0.0, 'PM2.5': 0.0}
        },
        "consumption": CONSUMPTION['summary'],
        "heat": 1000000.0
    })

    # no conflicting meta, same location, but overlapping time window
    FIRE_OVERLAPPING_TIME_WINDOWS = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'bar'},
        "start": datetime.datetime(2015,8,4,18,0,0),
        "end": datetime.datetime(2015,8,4,20,0,0),
        "area": 120.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T18:00:00": PLUMERISE_HOUR,
            "2015-08-04T19:00:00": EMPTY_PLUMERISE_HOUR
        },
        "timeprofile": {
            "2015-08-04T18:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            },
            "2015-08-04T19:00:00": {
                "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T18:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
            "2015-08-04T19:00:00": {"CO": 0.0, 'PM2.5': 0.0}
        },
        "consumption": CONSUMPTION['summary'],
        "heat": 2000000.0
    })

    # contiguous time windows, no conflicting meta, same location
    FIRE_CONTIGUOUS_TIME_WINDOWS = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'bar', 'bar': 'asdasd'},
        "start": datetime.datetime(2015,8,4,19,0,0),
        "end": datetime.datetime(2015,8,4,21,0,0),
        "area": 100.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T19:00:00": PLUMERISE_HOUR,
            "2015-08-04T20:00:00": EMPTY_PLUMERISE_HOUR
        },
        "timeprofile": {
            "2015-08-04T19:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            },
            "2015-08-04T20:00:00": {
                "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 10.0, 'CO2': 3.0}, "residual": {"PM2.5": 10.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T19:00:00": {"CO": 0.0, "PM2.5": 5.0},  # == 10.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
            "2015-08-04T20:00:00": {"CO": 0.0, 'PM2.5': 0.0}
        },
        "consumption": CONSUMPTION['summary'],
        "heat": 3000000.0
    })

    # non contiguous time windows, no conflicting meta, same location
    FIRE_NON_CONTIGUOUS_TIME_WINDOWS = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'bar', 'bar': 'sdf'},
        "start": datetime.datetime(2015,8,4,20,0,0),
        "end": datetime.datetime(2015,8,4,22,0,0),
        "area": 120.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T20:00:00": PLUMERISE_HOUR,
            "2015-08-04T21:00:00": EMPTY_PLUMERISE_HOUR
        },
        "timeprofile": {
            "2015-08-04T20:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            },
            "2015-08-04T21:00:00": {
                "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T20:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
            "2015-08-04T21:00:00": {"CO": 0.0, 'PM2.5': 0.0}
        },
        "consumption": CONSUMPTION['summary'],
        "heat": 4000000.0
    })

    FIRE_CONFLICTING_META = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'baz'},
        "start": datetime.datetime(2015,8,4,20,0,0),
        "end": datetime.datetime(2015,8,4,22,0,0),
        "area": 120.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T20:00:00": PLUMERISE_HOUR,
            "2015-08-04T21:00:00": EMPTY_PLUMERISE_HOUR
        },
        "timeprofile": {
            "2015-08-04T20:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            },
            "2015-08-04T21:00:00": {
                "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T20:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
            "2015-08-04T21:00:00": {"CO": 0.0, 'PM2.5': 0.0}
        },
        "consumption": CONSUMPTION['summary'],
        "heat": 5000000.0
    })

    FIRE_DIFFERENT_LAT_LNG = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {},
        "start": datetime.datetime(2015,8,4,20,0,0),
        "end": datetime.datetime(2015,8,4,22,0,0),
        "area": 120.0, "latitude": 47.0, "longitude": -121.0, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T20:00:00": PLUMERISE_HOUR,
            "2015-08-04T21:00:00": EMPTY_PLUMERISE_HOUR
        },
        "timeprofile": {
            "2015-08-04T20:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            },
            "2015-08-04T21:00:00": {
                "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T20:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
            "2015-08-04T21:00:00": {"CO": 0.0, 'PM2.5': 0.0}
        },
        "consumption": CONSUMPTION['summary'],
        "heat": 6000000.0
    })

    # def setup(self):
    #     pass

    ## Cases that do *not* merge

    def test_one_fire(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        merged_fires = firemerge.FireMerger().merge([self.FIRE_1])

        assert len(merged_fires) == 1
        assert merged_fires == [self.FIRE_1]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1

    def test_differenent_lat_lng(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_different_lat_lng = copy.deepcopy(self.FIRE_DIFFERENT_LAT_LNG)

        # shouldn't be merged
        merged_fires = firemerge.FireMerger().merge([self.FIRE_1, self.FIRE_DIFFERENT_LAT_LNG])

        assert len(merged_fires) == 2
        assert merged_fires == [self.FIRE_1, self.FIRE_DIFFERENT_LAT_LNG]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_DIFFERENT_LAT_LNG == original_fire_different_lat_lng

    def test_overlapping_time_windows(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_overlapping_time_windows = copy.deepcopy(self.FIRE_OVERLAPPING_TIME_WINDOWS)

        # shouldn't be merged
        merged_fires = firemerge.FireMerger().merge([self.FIRE_1, self.FIRE_OVERLAPPING_TIME_WINDOWS])

        assert len(merged_fires) == 2
        assert merged_fires == [self.FIRE_1, self.FIRE_OVERLAPPING_TIME_WINDOWS]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_OVERLAPPING_TIME_WINDOWS == original_overlapping_time_windows

    def test_conflicting_meta(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_conflicting_meta = copy.deepcopy(self.FIRE_CONFLICTING_META)

        # shouldn't be merged
        merged_fires = firemerge.FireMerger().merge([self.FIRE_1, self.FIRE_CONFLICTING_META])

        assert len(merged_fires) == 2
        assert merged_fires == [self.FIRE_1, self.FIRE_CONFLICTING_META]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_CONFLICTING_META == original_fire_conflicting_meta

    ## Cases that merge

    def test_non_contiguous_time_windows(self, monkeypatch):
        monkeypatch.setattr(uuid, 'uuid4', lambda: '1234abcd')

        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_non_contiguous_time_windows = copy.deepcopy(self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS)

        # *should* be merged
        merged_fires = firemerge.FireMerger().merge([self.FIRE_1, self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS])

        expected_merged_fires = [
            Fire({
                "id": "1234abcd",
                "original_fire_ids": {"SF11C14225236095807750"},
                "meta": {'foo': 'bar', 'bar': 'sdf'},
                "start": datetime.datetime(2015,8,4,17,0,0),
                "end": datetime.datetime(2015,8,4,22,0,0),
                "area": 240.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
                "plumerise": {
                    "2015-08-04T17:00:00": PLUMERISE_HOUR,
                    "2015-08-04T18:00:00": EMPTY_PLUMERISE_HOUR,
                    "2015-08-04T20:00:00": PLUMERISE_HOUR,
                    "2015-08-04T21:00:00": EMPTY_PLUMERISE_HOUR
                },
                "timeprofile": {
                    "2015-08-04T17:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T18:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    },
                    "2015-08-04T20:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T21:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    }
                },
                "emissions": {
                    "flaming": {"PM2.5": 10.0},
                    "residual": {"PM2.5": 20.0, 'CO': 2.0},
                    "smoldering": {"PM2.5": 40.0}
                },
                "timeprofiled_emissions": {
                    "2015-08-04T17:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
                    "2015-08-04T18:00:00": {"CO": 0.0, 'PM2.5': 0.0},
                    "2015-08-04T20:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
                    "2015-08-04T21:00:00": {"CO": 0.0, 'PM2.5': 0.0}
                },
                "consumption": {k: 2*v for k,v in CONSUMPTION['summary'].items()},
                "heat": 5000000.0
            })
        ]

        assert len(merged_fires) == len(expected_merged_fires)
        assert merged_fires == expected_merged_fires

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS == original_fire_non_contiguous_time_windows

    def test_contiguous_time_windows(self, monkeypatch):
        monkeypatch.setattr(uuid, 'uuid4', lambda: '1234abcd')

        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_contiguous_time_windows = copy.deepcopy(self.FIRE_CONTIGUOUS_TIME_WINDOWS)

        # *should* be merged
        merged_fires = firemerge.FireMerger().merge([self.FIRE_1, self.FIRE_CONTIGUOUS_TIME_WINDOWS])

        expected_merged_fires = [
            Fire({
                "id": "1234abcd",
                "original_fire_ids": {"SF11C14225236095807750"},
                "meta": {'foo': 'bar', 'bar': 'asdasd'},
                "start": datetime.datetime(2015,8,4,17,0,0),
                "end": datetime.datetime(2015,8,4,21,0,0),
                "area": 220.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
                "plumerise": {
                    "2015-08-04T17:00:00": PLUMERISE_HOUR,
                    "2015-08-04T18:00:00": EMPTY_PLUMERISE_HOUR,
                    "2015-08-04T19:00:00": PLUMERISE_HOUR,
                    "2015-08-04T20:00:00": EMPTY_PLUMERISE_HOUR
                },
                "timeprofile": {
                    "2015-08-04T17:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T18:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    },
                    "2015-08-04T19:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T20:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    }
                },
                "emissions": {
                    "flaming": {"PM2.5": 15.0, 'CO2': 3.0},
                    "residual": {"PM2.5": 20.0, 'CO': 2.0},
                    "smoldering": {"PM2.5": 40.0}
                },
                "timeprofiled_emissions": {
                    "2015-08-04T17:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
                    "2015-08-04T18:00:00": {"CO": 0.0, 'PM2.5': 0.0},
                    "2015-08-04T19:00:00": {"CO": 0.0, "PM2.5": 5.0},  # == 10.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
                    "2015-08-04T20:00:00": {"CO": 0.0, 'PM2.5': 0.0}
                },
                "consumption": {k: 2*v for k,v in CONSUMPTION['summary'].items()},
                "heat": 4000000.0
            })
        ]

        assert len(merged_fires) == len(expected_merged_fires)
        assert merged_fires == expected_merged_fires

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_CONTIGUOUS_TIME_WINDOWS == original_fire_contiguous_time_windows

    def test_all(self, monkeypatch):
        monkeypatch.setattr(uuid, 'uuid4', lambda: '1234abcd')

        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_overlapping_time_windows = copy.deepcopy(self.FIRE_OVERLAPPING_TIME_WINDOWS)
        original_fire_contiguous_time_windows = copy.deepcopy(self.FIRE_CONTIGUOUS_TIME_WINDOWS)
        original_fire_non_contiguous_time_windows = copy.deepcopy(self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS)
        original_fire_conflicting_meta = copy.deepcopy(self.FIRE_CONFLICTING_META)
        original_fire_different_lat_lng = copy.deepcopy(self.FIRE_DIFFERENT_LAT_LNG)

        merged_fires = firemerge.FireMerger().merge([
            self.FIRE_1,
            self.FIRE_OVERLAPPING_TIME_WINDOWS,
            self.FIRE_CONTIGUOUS_TIME_WINDOWS,
            self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS,
            self.FIRE_CONFLICTING_META,
            self.FIRE_DIFFERENT_LAT_LNG
        ])

        expected_merged_fires = [
            # FIRE_1 merged with FIRE_CONTIGUOUS_TIME_WINDOWS
            Fire({
                "id": "1234abcd",
                "original_fire_ids": {"SF11C14225236095807750"},
                "meta": {'foo': 'bar', 'bar': 'asdasd'},
                "start": datetime.datetime(2015,8,4,17,0,0),
                "end": datetime.datetime(2015,8,4,21,0,0),
                "area": 220.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
                "plumerise": {
                    "2015-08-04T17:00:00": PLUMERISE_HOUR,
                    "2015-08-04T18:00:00": EMPTY_PLUMERISE_HOUR,
                    "2015-08-04T19:00:00": PLUMERISE_HOUR,
                    "2015-08-04T20:00:00": EMPTY_PLUMERISE_HOUR
                },
                "timeprofile": {
                    "2015-08-04T17:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T18:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    },
                    "2015-08-04T19:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T20:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    }
                },
                "emissions": {
                    "flaming": {"PM2.5": 15.0, 'CO2': 3.0},
                    "residual": {"PM2.5": 20.0, 'CO': 2.0},
                    "smoldering": {"PM2.5": 40.0}
                },
                "timeprofiled_emissions": {
                    "2015-08-04T17:00:00": {"CO": 0.0, "PM2.5": 4.0},  # == 5.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
                    "2015-08-04T18:00:00": {"CO": 0.0, 'PM2.5': 0.0},
                    "2015-08-04T19:00:00": {"CO": 0.0, "PM2.5": 5.0},  # == 10.0 * 0.2 + 10.0 * 0.1 + 20.0 * 0.1
                    "2015-08-04T20:00:00": {"CO": 0.0, 'PM2.5': 0.0}
                },
                "consumption": {k: 2*v for k,v in CONSUMPTION['summary'].items()},
                "heat": 4000000.0
            }),
            # FIRE_OVERLAPPING_TIME_WINDOWS merged with
            # FIRE_NON_CONTIGUOUS_TIME_WINDOWS
            Fire({
                "id": "1234abcd",
                "original_fire_ids": {"SF11C14225236095807750"},
                "meta": {'foo': 'bar', 'bar': 'sdf'},
                "start": datetime.datetime(2015,8,4,18,0,0),
                "end": datetime.datetime(2015,8,4,22,0,0),
                "area": 240.0, "latitude": 47.41, "longitude": -121.41, "utc_offset": -7.0,
                "plumerise": {
                    "2015-08-04T18:00:00": PLUMERISE_HOUR,
                    "2015-08-04T19:00:00": EMPTY_PLUMERISE_HOUR,
                    "2015-08-04T20:00:00": PLUMERISE_HOUR,
                    "2015-08-04T21:00:00": EMPTY_PLUMERISE_HOUR
                },
                "timeprofile": {
                    "2015-08-04T18:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T19:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    },
                    "2015-08-04T20:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T21:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0, "residual": 0.0, "smoldering": 0.0
                    }
                },
                "emissions": {
                    "flaming": {"PM2.5": 10.0}, "residual": {"PM2.5": 20.0}, "smoldering": {"PM2.5": 40.0}
                },
                "timeprofiled_emissions": {
                    "2015-08-04T18:00:00": {"CO": 0.0, "PM2.5": 4.0},
                    "2015-08-04T19:00:00": {"CO": 0.0, 'PM2.5': 0.0},
                    "2015-08-04T20:00:00": {"CO": 0.0, "PM2.5": 4.0},
                    "2015-08-04T21:00:00": {"CO": 0.0, 'PM2.5': 0.0}
                },
                "consumption": {k: 2*v for k,v in CONSUMPTION['summary'].items()},
                "heat": 6000000.0
            }),
            self.FIRE_CONFLICTING_META,
            self.FIRE_DIFFERENT_LAT_LNG
        ]

        assert len(merged_fires) == len(expected_merged_fires)
        assert merged_fires == expected_merged_fires

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_OVERLAPPING_TIME_WINDOWS == original_overlapping_time_windows
        assert self.FIRE_CONTIGUOUS_TIME_WINDOWS == original_fire_contiguous_time_windows
        assert self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS == original_fire_non_contiguous_time_windows
        assert self.FIRE_CONFLICTING_META == original_fire_conflicting_meta
        assert self.FIRE_DIFFERENT_LAT_LNG == original_fire_different_lat_lng

        # TODO: repeat, but with fires initially in different order


##
## PlumeMerge tests
##

class TestPlumeMergerBucketFires(object):

    def test(self):
        config = {
            "grid": {
                "spacing": 0.5,
                "boundary": {
                  "sw": { "lat": 30, "lng": -110 },
                  "ne": { "lat": 40, "lng": -120 }
                }
            }
        }
        pm = firemerge.PlumeMerger(config)
        fires = [
            Fire({'latitude': 32.0, 'longitude': -100}),
            Fire({'latitude': 36.22, 'longitude': -111.1}),
            Fire({'latitude': 32.2, 'longitude': -110}),
            Fire({'latitude': 32.2, 'longitude': -111.2}),
            Fire({'latitude': 36.1, 'longitude': -111.4}),
            Fire({'latitude': 36.4, 'longitude': -111.3})
        ]
        expected_as_sets = [
            set([Fire({'latitude': 32.0, 'longitude': -100})]),
            set([Fire({'latitude': 32.2, 'longitude': -110})]),
            set([Fire({'latitude': 32.2, 'longitude': -111.2})]),
            set([
                Fire({'latitude': 36.1, 'longitude': -111.4}),
                Fire({'latitude': 36.4, 'longitude': -111.1}),
                Fire({'latitude': 36.22, 'longitude': -111.3})
            ])
        ]
        actual = pm.merge(fires)
        assert [set(e) for e in actual] == expected_as_sets


class TestPlumeMergerMerge(object):

    fires =  Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'bar'},
        "start": datetime.datetime(2015,8,4,17,0,0),
        "end": datetime.datetime(2015,8,4,18,0,0),
        "area": 120.0, "latitude": 47.4, "longitude": -121.5, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T17:00:00": {
                "emission_fractions": [
                    0.01,0.05,0.05,0.05,0.05,0.05,
                    0.09,0.09,0.09,0.05,0.05,0.05,
                    0.05,0.05,0.05,0.05,0.05,0.05,
                    0.01,0.01
                ],
                "heights": [
                    100,200,260,319,379,438,
                    497,557,616,676,735,794,
                    854,913,973,1032,1091,1151,
                    1210,1270,1329
                ],
                "smolder_fraction": 0.05
            }
        },
        "timeprofile": {
            "2015-08-04T17:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0, 'CO': 2.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T17:00:00": {"CO": 0.0, "PM2.5": 10.0}
        },
        "consumption": {
            "flaming": 1311,
            "residual": 1449,
            "smoldering": 1267,
            "total": 4027
        }
        "heat": 1000000.0
    })

    # no conflicting meta, same location, but overlapping time window
    FIRE_OVERLAPPING_TIME_WINDOWS = Fire({
        "id": "SF11C14225236095807750-0",
        "original_fire_ids": {"SF11C14225236095807750"},
        "meta": {'foo': 'bar'},
        "start": datetime.datetime(2015,8,4,18,0,0),
        "end": datetime.datetime(2015,8,4,20,0,0),
        "area": 120.0, "latitude": 47.6, "longitude": -121.7, "utc_offset": -7.0,
        "plumerise": {
            "2015-08-04T17:00:00": {
                "emission_fractions": [
                    0.01,0.05,0.05,0.05,0.05,0.05,
                    0.09,0.09,0.09,0.05,0.05,0.05,
                    0.05,0.05,0.05,0.05,0.05,0.05,
                    0.01,0.01
                ],
                "heights": [
                    100,200,260,319,379,438,
                    497,557,616,676,735,794,
                    854,913,973,1032,1091,1151,
                    1210,1270,1329
                ],
                "smolder_fraction": 0.05
            }
        },
        "timeprofile": {
            "2015-08-04T17:00:00": {
                "area_fraction": 0.1, "flaming": 0.2, "residual": 0.1, "smoldering": 0.1
            }
        },
        "emissions": {
            "flaming": {"PM2.5": 5.0}, "residual": {"PM2.5": 10.0}, "smoldering": {"PM2.5": 20.0}
        },
        "timeprofiled_emissions": {
            "2015-08-04T17:00:00": {"CO": 0.0, "PM2.5": 4.0}
        },
        "consumption": {
            "flaming": 200,
            "residual": 100,
            "smoldering": 50,
            "total": 400
        }
        "heat": 2000000.0
    })
