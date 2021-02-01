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
            'CH4': array([0.64459607]),
            'CO': array([15.11681762]),
            'CO2': array([314.34360837]),
            'NH3': array([0.15689582]),
            'NMHC': array([0.]),
            'NMOC': array([5.09911411]),
            'NO': array([0.32324319]),
            'NO2': array([0.26464355]),
            'NOX': array([0.28165635]),
            'PM': array([0.]),
            'PM10': array([2.83518306]),
            'PM2.5': array([2.55191994]),
            'SO2': array([0.25519199])
        },
        'residual': {
            'CH4': array([0.63597235]),
            'CO': array([11.75585251]),
            'CO2': array([132.33922632]),
            'NH3': array([0.14579603]),
            'NMHC': array([0.]),
            'NMOC': array([2.26025746]),
            'NO': array([0.21785614]),
            'NO2': array([0.08798036]),
            'NOX': array([0.09049409]),
            'PM': array([0.]),
            'PM10': array([1.86648667]),
            'PM2.5': array([1.68000601]),
            'SO2': array([0.14495812])}
        ,
        'smoldering': {
            'CH4': array([1.14446127]),
            'CO': array([21.15519317]),
            'CO2': array([238.15047817]),
            'NH3': array([0.26236662]),
            'NMHC': array([0.]),
            'NMOC': array([4.06743646]),
            'NO': array([0.39204207]),
            'NO2': array([0.15832468]),
            'NOX': array([0.16284824]),
            'PM': array([0.]),
            'PM10': array([3.35882796]),
            'PM2.5': array([3.02324749]),
            'SO2': array([0.26085876])
        },
        'total': {
            'CH4': array([2.42502969]),
            'CO': array([48.0278633]),
            'CO2': array([684.83331286]),
            'NH3': array([0.56505847]),
            'NMHC': array([0.]),
            'NMOC': array([11.42680803]),
            'NO': array([0.9331414]),
            'NO2': array([0.5109486]),
            'NOX': array([0.53499868]),
            'PM': array([0.]),
            'PM10': array([8.06049769]),
            'PM2.5': array([7.25517344]),
            'SO2': array([0.66100888])
        }
    }

    EXPECTED_FIRE1_EMISSIONS_PM_ONLY = {
        'flaming': {
            'PM10': array([ 2.8351830576]),
            'PM2.5': array([ 2.5519199438617])
        },
        'residual': {
            'PM10': array([ 1.866486673905]),
            'PM2.5': array([ 1.680006007115])
        },
        'smoldering': {
            'PM10': array([ 3.35882796256]),
            'PM2.5': array([ 3.02324749105])
        },
        'total': {
            'PM10': array([ 8.0604976940957]),
            'PM2.5': array([ 7.25517344203])
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
