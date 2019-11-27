"""Unit tests for bluesky.modules.emissions"""

__author__ = "Joel Dubowy"

import copy
#from unittest import mock

from numpy import array
from numpy.testing import assert_approx_equal
from py.test import raises

import afconfig

from bluesky.config import Config
from bluesky.models.fires import Fire
from bluesky.modules import emissions

FIRES = [
    Fire({
        'source': 'GOES-16',
        'type': "wf",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-04:00",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  0,
                        "specified_points": [
                            {
                                'area': 47.20000000000001,
                                'lat': 50.632,
                                'lng': -71.362,


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
                            }
                        ]
                    }
                ]
            }
        ]
    }),
    Fire({
        'type': "rx",
        "activity":  [
            {
                "active_areas": [
                    {
                        "start": "2018-06-27T00:00:00",
                        "end": "2018-06-28T00:00:00",
                        "ignition_start": "2018-06-27T09:00:00",
                        "ignition_end": "2018-06-28T11:00:00",
                        "utc_offset": "-07:00",
                        "ecoregion": "western",
                        'slope': 5,
                        'windspeed': 5,
                        'rain_days': 10,
                        'moisture_10hr': 50,
                        'fm_type':  "MEAS-Th",
                        'moisture_1khr': 50,
                        'moisture_duff': 50,
                        'moisture_litter': 30,
                        'canopy_consumption_pct':  0,
                        'shrub_blackened_pct':  50,
                        'pile_blackened_pct':  0,
                        "specified_points": [
                            {
                                'area': 50.4,
                                'lat': 45.632,
                                'lng': -120.362,
                                #[-120.3, 45.22]

                                "fuelbeds": [
                                    {
                                        "fccs_id": "52",
                                        "pct": 100.0,
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
                                        },
                                        # heat required by CONSUME
                                        "heat": {
                                            "flaming": [
                                                159765789.2311308
                                            ],
                                            "residual": [
                                                0.0
                                            ],
                                            "smoldering": [
                                                13157759.100788476
                                            ],
                                            "total": [
                                                172923548.3319193
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    })
]

class fire_failure_manager(object):
    def __init__(self, fire):
        self._fire = fire

    def __enter__(self):
        pass

    def __exit__(self, e_type, value, tb):
        if e_type:
            self._fire['error'] = str(value)
        return True # return true even if there's an error

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

    def test_wo_details(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")

        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_wo_details_PM_only(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self, reset_config):
        Config().set("feps", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        emissions.Feps(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

class TestPrichardOneillEmissions(BaseEmissionsTest):

    EXPECTED_FIRE1_EMISSIONS = {
        'flaming': {
            'CH4': [1.4589720000000002],
            'CO': [31.521],
            'CO2': [479.7196],
            'NH3': [0.45930600000000005],
            'NOx': [0.6184120000000001],
            'PM10': [6.223926520000001],
            'PM2.5': [5.274514],
            'SO2': [0.318212]
        },
        'residual': {
            'CH4': [0.0],
            'CO': [0.0],
            'CO2': [0.0],
            'NH3': [0.0],
            'NOx': [0.0],
            'PM10': [0.0],
            'PM2.5': [0.0],
            'SO2': [0.0]
        },
        'smoldering': {
            'CH4': [4.37643],
            'CO': [94.5525],
            'CO2': [1438.999],
            'NH3': [1.3777650000000001],
            'NOx': [1.85503],
            'PM10': [18.6697063],
            'PM2.5': [15.821785],
            'SO2': [0.9545300000000001]
        },
        'total': {
            'CH4': [5.835402],
            'CO': [126.0735],
            'CO2': [1918.7186000000002],
            'NH3': [1.8370710000000001],
            'NOx': [2.473442],
            'PM10': [24.893632820000004],
            'PM2.5': [21.096299],
            'SO2': [1.2727420000000003]
        }
    }

    SPECIES = ['CH4','CO','CO2','NH3','NOx','PM10','PM2.5','SO2','VOC']

    # Note: no tests with all emissions species, since that would be
    # a huge set

    def test_wo_details_PM_only(self, reset_config):
        Config().set("prichard-oneill", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        Config().set(self.SPECIES, 'emissions', "species")
        emissions.PrichardOneill(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self, reset_config):
        Config().set("prichard-oneill", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(self.SPECIES, 'emissions', "species")
        emissions.PrichardOneill(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

class TestConsumeEmissions(BaseEmissionsTest):

    EXPECTED_FIRE1_EMISSIONS = {
        'flaming': {
            'CH4': array([ 0.28354666]),
            'CO': array([ 8.41188426]),
            'CO2': array([ 321.44739737]),
            'NMHC': array([ 0.34025599]),
            'PM': array([ 1.77689241]),
            'PM10': array([ 1.08692886]),
            'PM2.5': array([ 0.94515553])
        },
        'residual': {
            'CH4': array([ 0.61167301]),
            'CO': array([ 11.94019232]),
            'CO2': array([ 124.47126801]),
            'NMHC': array([ 0.40219595]),
            'PM': array([ 2.03611701]),
            'PM10': array([ 1.53756161]),
            'PM2.5': array([ 1.43282308])
        },
        'smoldering': {
            'CH4': array([ 1.1007335]),
            'CO': array([ 21.48692107]),
            'CO2': array([ 223.99172808]),
            'NMHC': array([ 0.72376997]),
            'PM': array([ 3.66408549]),
            'PM10': array([ 2.76691229]),
            'PM2.5': array([ 2.57843053])
        },
        'total': {
            'CH4': array([ 1.99595317]),
            'CO': array([ 41.83899765]),
            'CO2': array([ 669.91039346]),
            'NMHC': array([ 1.46622192]),
            'PM': array([ 7.4770949]),
            'PM10': array([ 5.39140276]),
            'PM2.5': array([ 4.95640914])
        }
    }


    EXPECTED_FIRE1_EMISSIONS_PM_ONLY = {
        'flaming': {
            'PM10': array([ 1.08692886]),
            'PM2.5': array([ 0.94515553])
        },
        'residual': {
            'PM10': array([ 1.53756161]),
            'PM2.5': array([ 1.43282308])
        },
        'smoldering': {
            'PM10': array([ 2.76691229]),
            'PM2.5': array([ 2.57843053])
        },
        'total': {
            'PM10': array([ 5.39140276]),
            'PM2.5': array([ 4.95640914])
        }
    }

    def test_wo_details(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_wo_details_PM_only(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details_PM_only(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        Config().set(['PM2.5', 'PM10'], 'emissions', "species")
        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])
