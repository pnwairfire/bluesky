"""Unit tests for bluesky.extrafilewriters.emissionscsv"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.config import Config
from bluesky.extrafilewriters import emissionscsv
from bluesky.models.fires import Fire


FIRE_NO_LOCATIONS = Fire({
    "fuel_type": "natural",
    "id": "SF11C14225236095807750",
    "type": "wildfire",
    "activity": [
        {
            "active_areas": []
        }
    ]
})

FIRE_MISSING_TIMEPROFILE = Fire({
    "activity": [
        {
            "active_areas": [
                {
                    "start": "2015-01-20T17:00:00",
                    "end": "2015-01-21T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "specified_points": [
                        {
                            "lat": 45,
                            "lng": -119,
                            "area": 123,
                            "fuelbeds": [
                                {
                                    "emissions": {
                                        "flaming": {"PM2.5": [10.0]},
                                        "smoldering": {"PM2.5": [5.0]},
                                        "residual": {"PM2.5": [20.0]},
                                        "total": {"PM2.5": [35.0]}
                                    },
                                    "fccs_id": "9",
                                    "pct": 100.0
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    ]
})

FIRE_MISSING_EMISSIONS = Fire({
    "activity": [
        {
            "active_areas": [
                {
                    "start": "2015-01-20T17:00:00",
                    "end": "2015-01-21T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "specified_points": [
                        {
                            "lat": 45,
                            "lng": -119,
                            "area": 123,
                            "fuelbeds": [
                                {
                                    "fccs_id": "9",
                                    "pct": 100.0
                                }
                            ]
                        }
                    ],
                    "timeprofile": {
                        "2015-08-04T17:00:00": {
                            "area_fraction": 0.1,
                            "flaming": 0.2,
                            "smoldering": 0.3,
                            "residual": 0.1
                        }
                    }
                }
            ]
        }
    ]
})

FIRE = Fire({
    "fuel_type": "natural",
    "id": "SF11C14225236095807750",
    "type": "wildfire",
    "activity": [
        {
            "active_areas": [
                {
                    "start": "2015-08-04T17:00:00",
                    "end": "2015-08-05T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "specified_points": [
                        {
                            "lat": 47.41,
                            "lng": -121.41,
                            "area": 120.0,
                            "fuelbeds": [
                                {
                                    "emissions": {
                                        "flaming": {"PM2.5": [10.0]},
                                        "smoldering": {"PM2.5": [5.0]},
                                        "residual": {"PM2.5": [20.0]},
                                        "total": {"PM2.5": [35.0]}
                                    },
                                    "fccs_id": "9",
                                    "pct": 100.0
                                }
                            ],
                            "heat": {
                                "summary": {
                                    "flaming": 1000000000.0,
                                    "smoldering": 4000000000.0,
                                    "residual": 3000000000.0,
                                    "total": 8000000000.0
                                }
                            },
                            "plumerise": {
                                "2015-08-04T17:00:00": {
                                    "emission_fractions": [
                                        0.01,0.05,0.05,0.05,0.05,0.05,
                                        0.09,0.09,0.09,0.05,0.05,0.05,
                                        0.05,0.05,0.05,0.05,0.05,0.05,
                                        0.01,0.01
                                    ],
                                    "heights": [
                                        10, 20, 30, 40, 50, 60, 70, 80, 90, 100,
                                        110, 120, 130, 140, 150, 160, 170, 180,
                                        190, 200, 210
                                    ],
                                    "smolder_fraction": 0.05
                                }
                            },
                        }
                    ],
                    "timeprofile": {
                        "2015-08-04T17:00:00": {
                            "area_fraction": 0.1, "flaming": 0.2, "smoldering": 0.1, "residual": 0.1
                        },
                        "2015-08-04T18:00:00": {
                            "area_fraction": 0.3, "flaming": 0.1, "smoldering": 0.4, "residual": 0.2
                        }

                    }
                },
                {
                    "start": "2015-08-05T17:00:00",
                    "end": "2015-08-06T17:00:00",
                    "ecoregion": "southern",
                    "utc_offset": "-07:00",
                    "specified_points": [
                        {
                            "lat": 48.0,
                            "lng": -121.0,
                            "area": 102.0,
                            "fuelbeds": [
                                {
                                    "emissions": {
                                        "flaming": {"PM2.5": [100.0]},
                                        "smoldering": {"PM2.5": [50.0]},
                                        "residual": {"PM2.5": [200.0]},
                                        "total": {"PM2.5": [350.0]}
                                    },
                                    "fccs_id": "9",
                                    "pct": 100.0
                                }
                            ],
                            "heat": {
                                "summary": {
                                    "flaming": 2000000000.0,
                                    "smoldering": 6000000000.0,
                                    "residual": 1000000000.0,
                                    "total": 9000000000.0
                                }
                            },
                        }
                    ],
                    "timeprofile": {
                        "2015-08-05T17:00:00": {
                            "area_fraction": 0.3, "flaming": 0.1, "smoldering": 0.4, "residual": 0.2
                        }
                    }
                }
            ],
        }
    ]
})


class MockEmissionsWriter(object):
    def __init__(self):
        self.rows = []

    def writerow(self, list_of_values):
        self.rows.append(list_of_values)


class TestEmissionsCsvWriterWriteFire(object):

    def setup(self):
        Config().set('foo.csv', 'extrafiles', 'emissionscsv', 'filename')
        self.writer = emissionscsv.EmissionsCsvWriter('/tmp/')
        self.writer.emissions_writer = MockEmissionsWriter()

    def test_no_locations(self, reset_config):
        with raises(ValueError) as e_info:
            self.writer._write_fire(FIRE_NO_LOCATIONS)
        assert e_info.value.args[0] == emissionscsv.EmissionsCsvWriter.MISSING_LOCATONS_ERROR_MSG

    def test_no_timeprofile(self, reset_config):
        with raises(ValueError) as e_info:
            self.writer._write_fire(FIRE_MISSING_TIMEPROFILE)
        assert e_info.value.args[0] == emissionscsv.EmissionsCsvWriter.MISSING_TIMEPROFILE_ERROR_MSG

    def test_no_emissions(self, reset_config):
        with raises(ValueError) as e_info:
            self.writer._write_fire(FIRE_MISSING_EMISSIONS)
        assert e_info.value.args[0] == emissionscsv.EmissionsCsvWriter.MISSING_EMISSIONS_ERROR_MSG

    def test_one_fire_two_points_one_with_emissions(self, reset_config):
        self.writer._write_fire(FIRE)

        expected_rows = [
            [
                'SF11C14225236095807750', '0', '', '2015-08-04T17:00:00-07:00',
                # time profiles - area fract, flaming, smoldering, residual
                0.1, 0.2, 0.1, 0.1,
                4.5, '', '', '', '', '', '', '', '', # emissions - emitted (i.e. total)
                2.0, '', '', '', '', '', '', '', '', # emissions - flaming
                0.5, '', '', '', '', '', '', '', '', # emissions - smoldering
                2.0, '', '', '', '', '', '', '', '',  # emissions - residual
                0.05, 800000000.0, # smoldering fraction, heat
                # the rest are plumerise heights
                10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110,
                120, 130, 140, 150, 160, 170, 180, 190, 200, 210
            ],
            [
                'SF11C14225236095807750', '1', '', '2015-08-04T18:00:00-07:00',
                # time profiles - area fract, flaming, smoldering, residual
                0.3, 0.1, 0.4, 0.2,
                7.0, '', '', '', '', '', '', '', '', # emissions - emitted (i.e. total)
                1.0, '', '', '', '', '', '', '', '', # emissions - flaming
                2.0, '', '', '', '', '', '', '', '', # emissions - smoldering
                4.0, '', '', '', '', '', '', '', '',  # emissions - residual
                '', 2400000000.0, # smoldering fraction, heat
                # the rest are plumerise heights
                '', '', '', '', '', '', '', '', '', '', '',
                '', '', '', '', '', '', '', '', '', ''
            ],
            [
                'SF11C14225236095807750', '0', '', '2015-08-05T17:00:00-07:00',
                # time profiles - area fract, flaming, smoldering, residual
                 0.3, 0.1, 0.4, 0.2,
                 70.0, '', '', '', '', '', '', '', '', # emissions - emitted (i.e. total)
                 10.0, '', '', '', '', '', '', '', '', # emissions - flaming
                 20.0, '', '', '', '', '', '', '', '', # emissions - smoldering
                 40.0, '', '', '', '', '', '', '', '',  # emissions - residual
                 '', 2700000000.0, # smoldering fraction, heat
                # the rest are plumerise heights
                 '', '', '', '', '', '', '', '', '', '', '',
                 '', '', '', '', '', '', '', '', '', ''
            ]
        ]

        assert self.writer.emissions_writer.rows == expected_rows
