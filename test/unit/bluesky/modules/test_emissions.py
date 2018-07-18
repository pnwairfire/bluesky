"""Unit tests for bluesky.modules.emissions"""

__author__ = "Joel Dubowy"

import copy
#from unittest import mock

from numpy.testing import assert_approx_equal
from py.test import raises

import afconfig

from bluesky.models.fires import Fire
from bluesky.modules import emissions

FIRES = [
    {
        'source': 'GOES-16',
        'type': "wf",
        "growth":  [
            {
                # timeprofile should be ignored and replcaced when running
                # FRP emissions
                "timeprofile": {
                    "2018-06-27T17:00:00": {
                        'area_fraction': 0.75,
                        'flaming': 0.75,
                        'smoldering': 0.3,
                        'residual': 0.0
                    },
                    "2018-06-27T20:00:00": {
                        'area_fraction': 0.25,
                        'flaming': 0.25,
                        'smoldering': 0.7,
                        'residual': 1.0
                    }
                },
                # Hourly FRP is used for FRP emissions
                "hourly_frp": {
                    "2018-06-27T10:00:00": 55.4,
                    "2018-06-27T11:00:00": 66,
                    "2018-06-27T12:00:00": 78,
                    "2018-06-27T13:00:00": 83,
                    "2018-06-27T18:00:00": 82,
                    "2018-06-27T19:00:00": 66,
                    "2018-06-27T20:00:00": 52.5
                },
                #55.4 + 66 + 78 + 83 + 82 + 66 + 52.5 = 482.9
                "frp": 482.9,
                "location": {
                    'area': 47.20000000000001,
                    "geojson": {
                        "type": "Point",
                        "coordinates": [-71.362, 50.632],
                    },
                    "utc_offset": "-04:00"
                },
                "start": "2018-06-27T00:00:00",
                "end": "2018-06-28T00:00:00"
            }
        ]
    },
    {
        'type': "rx",
        "growth":  [
            {
                "location": {
                    'area': 50.4,
                    "geojson": {
                        "type": "MultiPoint",
                        "coordinates": [
                            [-120.362, 45.632],
                            [-120.3, 45.22]
                        ]
                    },
                    "utc_offset": "-07:00"
                },
                "start": "2018-06-27T00:00:00",
                "end": "2018-06-28T00:00:00",
                "fuelbeds": [
                    {
                        "consumption": {

                            "foo": {
                                "bar": {
                                    "smoldering": [0.0],
                                    "residual": [200.4],
                                    "flaming": [0.0]
                                },
                                "baz": {
                                    "smoldering": [900.5],
                                    "residual": [800.0],
                                    "flaming": [100.2]
                                }
                            },
                            "boo": {
                                "blem": {
                                    "smoldering": [0.0],
                                    "residual": [0.0],
                                    "flaming": [200]
                                }
                            }
                        }
                    }
                ]
            }
        ]
    }
]

class fire_failure_manager(object):
    def __init__(self, fire):
        self._fire = fire

    def __enter__(self):
        pass

    def __exit__(self, e_type, value, tb):
        self._fire['error'] = str(value)
        return True # just skip

def create_config_getter(config):
    def _get(*keys, **kwargs):
        return afconfig.get_config_value(config, *keys, **kwargs)
    return _get

class BaseEmissionsTest(object):

    def setup(self):
        self.fires = copy.deepcopy(FIRES)

    def _check_emissions(self, expected, actual):
        assert set(expected.keys()) == set(actual.keys())
        for p in expected:
            assert set(expected[p].keys()) == set(actual[p].keys())
            for s in expected[p]:
                assert_approx_equal(expected[p][s][0], actual[p][s][0])

class TestFepsEmissions(BaseEmissionsTest):

    EXPECTED_FIRE1_EMISSIONS = {
        'flaming': {
            'CH4': [1.146763999999999],
            'CO': [21.554359999999996],
            'CO2': [495.23994],
            'NH3': [0.3621612799999999],
            'NOx': [0.7264840000000004],
            'PM10': [2.5788380799999997],
            'PM2.5': [2.1854560000000007],
            'SO2': [0.294196],
            'VOC': [5.206068399999999]
        },
        'residual': {
            'CH4': [9.871947200000001],
            'CO': [210.20404799999997],
            'CO2': [1393.6372320000003],
            'NH3': [3.4119242240000003],
            'NOx': [0.9083631999999999],
            'PM10': [19.633610303999998],
            'PM2.5': [16.6386528],
            'SO2': [0.980392],
            'VOC': [49.04641072000001]
        },
        'smoldering': {
            'CH4': [8.886134000000002],
            'CO': [189.21305999999998],
            'CO2': [1254.46854],
            'NH3': [3.07120928],
            'NOx': [0.817654],
            'PM10': [17.67299688],
            'PM2.5': [14.977116],
            'SO2': [0.88249],
            'VOC': [44.14863340000001]
        },
        'total': {
            'CH4': [19.9048452],
            'CO': [420.97146799999996],
            'CO2': [3143.3457120000003],
            'NH3': [6.845294784],
            'NOx': [2.4525012000000004],
            'PM10': [39.885445264],
            'PM2.5': [33.8012248],
            'SO2': [2.157078],
            'VOC': [98.40111252000001]
        }
    }

    EXPECTED_FIRE1_EMISSIONS_PM_ONLY = {
        'flaming': {
            'PM10': [2.5788380799999997],
            'PM2.5': [2.1854560000000007]
        },
        'residual': {
            'PM10': [19.633610303999998],
            'PM2.5': [16.6386528]
        },
        'smoldering': {
            'PM10': [17.67299688],
            'PM2.5': [14.977116]
        },
        'total': {
            'PM10': [39.885445264],
            'PM2.5': [33.8012248]
        }
    }

    def test_wo_details(self):
        config_getter = create_config_getter({
            "emissions": {
                "model": "feps",
                "include_emissions_details": False
            }
        })
        emissions.Feps(fire_failure_manager, config_getter).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['growth'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['growth'][0]['fuelbeds'][0]['emissions'])

    def test_with_details(self):
        config_getter = create_config_getter({
            "emissions": {
                "model": "feps",
                "include_emissions_details": True
            }
        })
        emissions.Feps(fire_failure_manager, config_getter).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['growth'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['growth'][0]['fuelbeds'][0]['emissions'])

    def test_wo_details_PM_only(self):
        config_getter = create_config_getter({
            "emissions": {
                "model": "feps",
                "include_emissions_details": False,
                'species': ['PM2.5', 'PM10']
            }
        })
        emissions.Feps(fire_failure_manager, config_getter).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['growth'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['growth'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self):
        config_getter = create_config_getter({
            "emissions": {
                "model": "feps",
                "include_emissions_details": True,
                'species': ['PM2.5', 'PM10']
            }
        })
        emissions.Feps(fire_failure_manager, config_getter).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['growth'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['growth'][0]['fuelbeds'][0]['emissions'])
