"""Unit tests for bluesky.dispersers.DispersionBase
"""

import copy
import datetime

from bluesky.config import Config
from bluesky.dispersers import DispersionBase
from bluesky.models import fires

class FakeDisperser(DispersionBase):

    def __init__(self, met_info):
        self._model = 'hysplit'

    def _required_activity_fields(self):
        return ('timeprofile', 'plumerise')

    def _run(wdir):
        pass

class TestDispersionBaseConfig(object):

    def setup(self):
        Config().set(2.2, "dispersion", "hysplit", "QCYCLE")
        Config().set(333, "dispersion", "hysplit", "numpar")
        Config().set(34, "dispersion", "hysplit", "FOO")
        Config().set(100, "dispersion", "hysplit", "bar")

        self.d = FakeDisperser({})

    def test_non_overridden_default(self):
        assert self.d.config('MGMIN') == 10
        assert self.d.config('mgmin') == 10

    def test_user_overridden_default_user_uppercase(self):
        assert self.d.config('QCYCLE') == 2.2
        assert self.d.config('qcycle') == 2.2

    def test_user_overridden_default_user_lowercase(self):
        assert self.d.config('NUMPAR') == 333
        assert self.d.config('numpar') == 333

    def test_user_defined_config_no_default_uppercase(self):
        assert self.d.config('FOO') == 34
        assert self.d.config('foo') == 34

    def test_user_defined_config_no_default_lowercase(self):
        assert self.d.config('BAR') == 100
        assert self.d.config('bar') == 100


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


class TestDispersionBaseSetFireData(object):

    def setup(self):
        self.d = FakeDisperser({})
        self.d._model_start = datetime.datetime(2015, 8, 5, 0, 0, 0)
        self.d._num_hours = 2

    def test_one_activity_obj_one_active_area_one_specified_point(self):
        fire = fires.Fire({
            "fuel_type": "natural",
            "id": "SF11C14225236095807750",
            "type": "wildfire",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2015-08-04T17:00:00",
                            "end": "2015-08-05T17:00:00",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 120.0,
                                    "consumption": CONSUMPTION,
                                    "fuelbeds": [
                                        {
                                            "emissions": {
                                                "flaming": {"PM2.5": [9.545588271207714]},
                                                "residual": {"PM2.5": [24.10635856528243]},
                                                "smoldering": {"PM2.5": [21.073928205514225]},
                                                "total": {"PM2.5": [54.725875042004375]}
                                            },
                                            "fccs_id": "9",
                                            "heat": {
                                                "flaming": [20979314881.77519],
                                                "residual": [23190340130.141827],
                                                "smoldering": [20273139206.843895],
                                                "total": [64442794218.7609]
                                            },
                                            "pct": 100.0
                                        }
                                    ],
                                    "lat": 47.41,
                                    "lng": -121.41,
                                    "plumerise": {
                                        "2015-08-04T17:00:00": PLUMERISE_HOUR
                                    },
                                    "rain_days": 8,
                                    "slope": 20.0,
                                    "snow_month": 5,
                                    "sunrise_hour": 4,
                                    "sunset_hour": 19
                                }
                            ],
                            "state": "WA",
                            "timeprofile": {
                                "2015-08-04T17:00:00": {
                                    "area_fraction": 0.1, "flaming": 0.2,
                                    "residual": 0.1, "smoldering": 0.1
                                }
                            }
                        }
                    ],
                }
            ]
        })

        expected_fire = fires.Fire({
            "id": "SF11C14225236095807750-0",
            "meta": {},
            "start": "2015-08-04T17:00:00",
            "end": "2015-08-05T17:00:00",
            "area": 120.0,
            "latitude": 47.41,
            "longitude": -121.41,
            "utc_offset": -7.0,
            "plumerise": {
                "2015-08-04T17:00:00": PLUMERISE_HOUR,
                "2015-08-04T18:00:00": EMPTY_PLUMERISE_HOUR
            },
            "timeprofile": {
                "2015-08-04T17:00:00": {
                    "area_fraction": 0.1, "flaming": 0.2,
                    "residual": 0.1, "smoldering": 0.1
                },
                "2015-08-04T18:00:00": {
                    "area_fraction": 0.0, "flaming": 0.0,
                    "residual": 0.0, "smoldering": 0.0
                }
            },
            "emissions": {
                "flaming": {"PM2.5": 9.545588271207714},
                "residual": {"PM2.5": 24.10635856528243},
                "smoldering": {"PM2.5": 21.073928205514225}
            },
            "timeprofiled_emissions": {
                "2015-08-04T17:00:00": {
                    "CO": 0.0, "PM2.5": 6.427146331321209  # == 9.545588271207714 * 0.2 + 24.10635856528243 * 0.1 + 21.073928205514225 * 0.1
                },
                "2015-08-04T18:00:00": {
                    "CO": 0.0, 'PM2.5': 0.0
                }
            },
            "consumption": CONSUMPTION['summary'],
            "heat": 64442794218.7609
        })

        self.d._set_fire_data([fire])

        assert len(self.d._fires) == 1
        assert self.d._fires[0].keys() == expected_fire.keys()
        for k in self.d._fires[0].keys():
            assert self.d._fires[0][k] == expected_fire[k], "{} don't match".format(k)

    def test_two_activity_objs_one_active_area_same_specified_point(self):
        fire = fires.Fire({
            "fuel_type": "natural",
            "id": "SF11C14225236095807750",
            "type": "wildfire",
            "activity": [
                {
                    "active_areas": [
                        {
                            "start": "2015-08-04T17:00:00",
                            "end": "2015-08-04T18:00:00",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 120.0,
                                    "consumption": CONSUMPTION,
                                    "fuelbeds": [
                                        {
                                            "emissions": {
                                                "flaming": {"PM2.5": [9.545588271207714]},
                                                "residual": {"PM2.5": [24.10635856528243]},
                                                "smoldering": {"PM2.5": [21.073928205514225]},
                                                "total": {"PM2.5": [54.725875042004375]}
                                            },
                                            "fccs_id": "9",
                                            "heat": {
                                                "flaming": [20979314881.77519],
                                                "residual": [23190340130.141827],
                                                "smoldering": [20273139206.843895],
                                                "total": [64442794218.7609]
                                            },
                                            "pct": 100.0
                                        }
                                    ],
                                    "lat": 47.41,
                                    "lng": -121.41,
                                    "plumerise": {
                                        "2015-08-04T17:00:00": PLUMERISE_HOUR
                                    },
                                    "rain_days": 8,
                                    "slope": 20.0,
                                    "snow_month": 5,
                                    "sunrise_hour": 4,
                                    "sunset_hour": 19
                                }
                            ],
                            "state": "WA",
                            "timeprofile": {
                                "2015-08-04T17:00:00": {
                                    "area_fraction": 0.1, "flaming": 0.2,
                                    "residual": 0.1, "smoldering": 0.1
                                }
                            }
                        }
                    ],
                },
                {
                    "active_areas": [
                        {
                            "start": "2015-08-04T18:00:00",
                            "end": "2015-08-04T19:00:00",
                            "utc_offset": "-07:00",
                            "specified_points": [
                                {
                                    "area": 120.0,
                                    "consumption": CONSUMPTION,
                                    "fuelbeds": [
                                        {
                                            "emissions": {
                                                "flaming": {"PM2.5": [9.545588271207714]},
                                                "residual": {"PM2.5": [24.10635856528243]},
                                                "smoldering": {"PM2.5": [21.073928205514225]},
                                                "total": {"PM2.5": [54.725875042004375]}
                                            },
                                            "fccs_id": "9",
                                            "heat": {
                                                "flaming": [20979314881.77519],
                                                "residual": [23190340130.141827],
                                                "smoldering": [20273139206.843895],
                                                "total": [64442794218.7609]
                                            },
                                            "pct": 100.0
                                        }
                                    ],
                                    "lat": 47.41,
                                    "lng": -121.41,
                                    "plumerise": {
                                        "2015-08-04T18:00:00": PLUMERISE_HOUR
                                    },
                                    "rain_days": 8,
                                    "slope": 20.0,
                                    "snow_month": 5,
                                    "sunrise_hour": 4,
                                    "sunset_hour": 19
                                }
                            ],
                            "state": "WA",
                            "timeprofile": {
                                "2015-08-04T18:00:00": {
                                    "area_fraction": 0.1, "flaming": 0.2,
                                    "residual": 0.1, "smoldering": 0.1
                                }
                            }
                        }
                    ],
                }
            ]
        })

        expected_fires = [
            fires.Fire({
                "id": "SF11C14225236095807750-0",
                "meta": {},
                "start": "2015-08-04T17:00:00",
                "end": "2015-08-04T18:00:00",
                "area": 120.0,
                "latitude": 47.41,
                "longitude": -121.41,
                "utc_offset": -7.0,
                "plumerise": {
                    "2015-08-04T17:00:00": PLUMERISE_HOUR,
                    "2015-08-04T18:00:00": EMPTY_PLUMERISE_HOUR
                },
                "timeprofile": {
                    "2015-08-04T17:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2,
                        "residual": 0.1, "smoldering": 0.1
                    },
                    "2015-08-04T18:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0,
                        "residual": 0.0, "smoldering": 0.0
                    }
                },
                "emissions": {
                    "flaming": {"PM2.5": 9.545588271207714},
                    "residual": {"PM2.5": 24.10635856528243},
                    "smoldering": {"PM2.5": 21.073928205514225}
                },
                "timeprofiled_emissions": {
                    "2015-08-04T17:00:00": {
                        "CO": 0.0, "PM2.5": 6.427146331321209  # == 9.545588271207714 * 0.2 + 24.10635856528243 * 0.1 + 21.073928205514225 * 0.1
                    },
                    "2015-08-04T18:00:00": {
                        "CO": 0.0, 'PM2.5': 0.0
                    }
                },
                "consumption": CONSUMPTION['summary'],
                "heat": 64442794218.7609
            }),
            fires.Fire({
                "id": "SF11C14225236095807750-1",
                "meta": {},
                "start": "2015-08-04T18:00:00",
                "end": "2015-08-04T19:00:00",
                "area": 120.0,
                "latitude": 47.41,
                "longitude": -121.41,
                "utc_offset": -7.0,
                "plumerise": {
                    "2015-08-04T17:00:00": EMPTY_PLUMERISE_HOUR,
                    "2015-08-04T18:00:00": PLUMERISE_HOUR
                },
                "timeprofile": {
                    "2015-08-04T17:00:00": {
                        "area_fraction": 0.0, "flaming": 0.0,
                        "residual": 0.0, "smoldering": 0.0
                    },
                    "2015-08-04T18:00:00": {
                        "area_fraction": 0.1, "flaming": 0.2,
                        "residual": 0.1, "smoldering": 0.1
                    }
                },
                "emissions": {
                    "flaming": {"PM2.5": 9.545588271207714},
                    "residual": {"PM2.5": 24.10635856528243},
                    "smoldering": {"PM2.5": 21.073928205514225}
                },
                "timeprofiled_emissions": {
                    "2015-08-04T17:00:00": {
                        "CO": 0.0, "PM2.5": 0.0
                    },
                    "2015-08-04T18:00:00": {
                        "CO": 0.0, "PM2.5": 6.427146331321209  # == 9.545588271207714 * 0.2 + 24.10635856528243 * 0.1 + 21.073928205514225 * 0.1
                    }
                },
                "consumption": CONSUMPTION['summary'],
                "heat": 64442794218.7609
            })
        ]

        self.d._set_fire_data([fire])

        assert len(self.d._fires) == 2
        for i, f in enumerate(sorted(self.d._fires, key=lambda f:f['start'])):
            assert f.keys() == expected_fires[i].keys()
            for k in f.keys():
                assert f[k] == expected_fires[i][k], "{} don't match".format(k)

class TestDispersionBaseMergeFires(object):

    FIRE_1 = fires.Fire({
        "id": "SF11C14225236095807750-0",
        "meta": {'foo': 'bar'},
        "start": "2015-08-04T17:00:00", "end": "2015-08-04T19:00:00",
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
    FIRE_OVERLAPPING_TIME_WINDOWS = fires.Fire({
        "id": "SF11C14225236095807750-0",
        "meta": {'foo': 'bar'},
        "start": "2015-08-04T18:00:00", "end": "2015-08-04T20:00:00",
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
    FIRE_CONTIGUOUS_TIME_WINDOWS = fires.Fire({
        "id": "SF11C14225236095807750-0",
        "meta": {'foo': 'bar', 'bar': 'asdasd'},
        "start": "2015-08-04T19:00:00", "end": "2015-08-04T21:00:00",
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
    FIRE_NON_CONTIGUOUS_TIME_WINDOWS = fires.Fire({
        "id": "SF11C14225236095807750-0",
        "meta": {'foo': 'bar', 'bar': 'sdf'},
        "start": "2015-08-04T20:00:00", "end": "2015-08-04T22:00:00",
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

    FIRE_CONFLICTING_META = fires.Fire({
        "id": "SF11C14225236095807750-0",
        "meta": {'foo': 'baz'},
        "start": "2015-08-04T20:00:00", "end": "2015-08-04T22:00:00",
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

    FIRE_DIFFERENT_LAT_LNG = fires.Fire({
        "id": "SF11C14225236095807750-0",
        "meta": {},
        "start": "2015-08-04T20:00:00", "end": "2015-08-04T22:00:00",
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

    def setup(self):
        self.d = FakeDisperser({})
        # self.d._model_start = datetime.datetime(2015, 8, 5, 0, 0, 0)
        # self.d._num_hours = 2

    ## Cases that do *not* merge

    def test_one_fire(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        merged_fires = self.d._merge_fires([self.FIRE_1])

        assert len(merged_fires) == 1
        assert merged_fires == [self.FIRE_1]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1

    def test_differenent_lat_lng(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_different_lat_lng = copy.deepcopy(self.FIRE_DIFFERENT_LAT_LNG)

        # shouldn't be merged
        merged_fires = self.d._merge_fires([self.FIRE_1, self.FIRE_DIFFERENT_LAT_LNG])

        assert len(merged_fires) == 2
        assert merged_fires == [self.FIRE_1, self.FIRE_DIFFERENT_LAT_LNG]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_DIFFERENT_LAT_LNG == original_fire_different_lat_lng

    def test_overlapping_time_windows(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_overlapping_time_windows = copy.deepcopy(self.FIRE_OVERLAPPING_TIME_WINDOWS)

        # shouldn't be merged
        merged_fires = self.d._merge_fires([self.FIRE_1, self.FIRE_OVERLAPPING_TIME_WINDOWS])

        assert len(merged_fires) == 2
        assert merged_fires == [self.FIRE_1, self.FIRE_OVERLAPPING_TIME_WINDOWS]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_OVERLAPPING_TIME_WINDOWS == original_overlapping_time_windows

    def test_conflicting_meta(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_conflicting_meta = copy.deepcopy(self.FIRE_CONFLICTING_META)

        # shouldn't be merged
        merged_fires = self.d._merge_fires([self.FIRE_1, self.FIRE_CONFLICTING_META])

        assert len(merged_fires) == 2
        assert merged_fires == [self.FIRE_1, self.FIRE_CONFLICTING_META]

        # make sure input fire wasn't modified
        assert self.FIRE_1 == original_fire_1
        assert self.FIRE_CONFLICTING_META == original_fire_conflicting_meta

    ## Cases that merge

    def test_non_contiguous_time_windows(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_non_contiguous_time_windows = copy.deepcopy(self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS)

        # *should* be merged
        merged_fires = self.d._merge_fires([self.FIRE_1, self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS])

        expected_merged_fires = [
            fires.Fire({
                "id": "combined-fire-SF11C142-SF11C142",
                "meta": {'foo': 'bar', 'bar': 'sdf'},
                "start": "2015-08-04T17:00:00", "end": "2015-08-04T22:00:00",
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

    def test_contiguous_time_windows(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_fire_contiguous_time_windows = copy.deepcopy(self.FIRE_CONTIGUOUS_TIME_WINDOWS)

        # *should* be merged
        merged_fires = self.d._merge_fires([self.FIRE_1, self.FIRE_CONTIGUOUS_TIME_WINDOWS])

        expected_merged_fires = [
            fires.Fire({
                "id": "combined-fire-SF11C142-SF11C142",
                "meta": {'foo': 'bar', 'bar': 'asdasd'},
                "start": "2015-08-04T17:00:00", "end": "2015-08-04T21:00:00",
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

    def test_all(self):
        original_fire_1 = copy.deepcopy(self.FIRE_1)
        original_overlapping_time_windows = copy.deepcopy(self.FIRE_OVERLAPPING_TIME_WINDOWS)
        original_fire_contiguous_time_windows = copy.deepcopy(self.FIRE_CONTIGUOUS_TIME_WINDOWS)
        original_fire_non_contiguous_time_windows = copy.deepcopy(self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS)
        original_fire_conflicting_meta = copy.deepcopy(self.FIRE_CONFLICTING_META)
        original_fire_different_lat_lng = copy.deepcopy(self.FIRE_DIFFERENT_LAT_LNG)

        merged_fires = self.d._merge_fires([
            self.FIRE_1,
            self.FIRE_OVERLAPPING_TIME_WINDOWS,
            self.FIRE_CONTIGUOUS_TIME_WINDOWS,
            self.FIRE_NON_CONTIGUOUS_TIME_WINDOWS,
            self.FIRE_CONFLICTING_META,
            self.FIRE_DIFFERENT_LAT_LNG
        ])

        expected_merged_fires = [
            # FIRE_1 merged with FIRE_CONTIGUOUS_TIME_WINDOWS
            fires.Fire({
                "id": "combined-fire-SF11C142-SF11C142",
                "meta": {'foo': 'bar', 'bar': 'asdasd'},
                "start": "2015-08-04T17:00:00", "end": "2015-08-04T21:00:00",
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
            fires.Fire({
                "id": "combined-fire-SF11C142-SF11C142",
                "meta": {'foo': 'bar', 'bar': 'sdf'},
                "start": "2015-08-04T18:00:00", "end": "2015-08-04T22:00:00",
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