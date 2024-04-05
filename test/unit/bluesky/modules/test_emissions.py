"""Unit tests for bluesky.modules.emissions"""

__author__ = "Joel Dubowy"

import copy
#from unittest import mock

from numpy import array
from numpy.testing import assert_approx_equal
from pytest import raises

import afconfig

from bluesky.config import Config
from bluesky.models.fires import Fire
from bluesky.modules import emissions

from . import set_old_consume_defaults

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
                                            "canopy": {
                                                "midstory": {
                                                    "smoldering": [0.0],
                                                    "residual": [200.4],
                                                    "flaming": [0.0]
                                                },
                                                "overstory": {
                                                    "smoldering": [900.5],
                                                    "residual": [800.0],
                                                    "flaming": [100.2]
                                                }
                                            },
                                            "ground fuels": {
                                                "duff upper": {
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

class fire_failure_manager():
    def __init__(self, fire):
        self._fire = fire

    def __enter__(self):
        pass

    def __exit__(self, e_type, value, tb):
        if e_type:
            self._fire['error'] = str(value)
        return True # return true even if there's an error

class BaseEmissionsTest():

    def setup_method(self):
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
            'CO': [27.028606023103013],
            'SO2': [0.39522236726530535],
            'NOx': [0.5140925],
            'NH3': [0.32721800000000006],
            'CH4': [1.234943344888901],
            'PM2.5': [3.9625206441915526],
            'PM10': [6.223146000000001],
            'CO2': [494.6158285291992]
        },
        'smoldering': {
            'CO': [126.7501603486871],
            'SO2': [1.5593568283333363],
            'NOx': [0.97118925],
            'NH3': [1.6569200000000002],
            'CH4': [6.847284303487535],
            'PM2.5': [17.750671735337],
            'PM10': [18.667365000000004],
            'CO2': [1426.2988355961934]
        },
        'residual': {
            'CO': [0.0],
            'SO2': [0.0],
            'NOx': [0.0],
            'NH3': [0.0],
            'CH4': [0.0],
            'PM2.5': [0.0],
            'PM10': [0.0],
            'CO2': [0.0]
        },
        'total': {
            'CO': [153.7787663717901],
            'SO2': [1.9545791955986418],
            'NOx': [1.4852817500000002],
            'NH3': [1.9841380000000002],
            'CH4': [8.082227648376435],
            'PM2.5': [21.713192379528554],
            'PM10': [24.890511000000004],
            'CO2': [1920.9146641253924]
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
            'PM': array([0.]),
            'PM10': array([2.77209549]),
            'PM2.5': array([2.49513546]),
            'CO': array([17.01947807]),
            'CO2': array([311.45162419]),
            'CH4': array([0.77762394]),
            'NMHC': array([0.]),
            'NMOC': array([5.09911411]),
            'NH3': array([0.20604391]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.32371577]),
            'SO2': array([0.24886516])
        },
        'smoldering': {
            'PM': array([0.]),
            'PM10': array([3.30220825]),
            'PM2.5': array([2.97228466]),
            'CO': array([21.22384789]),
            'CO2': array([238.82849103]),
            'CH4': array([1.14655256]),
            'NMHC': array([0.]),
            'NMOC': array([4.06743646]),
            'NH3': array([0.27744516]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.16262207]),
            'SO2': array([0.26110856])
        },
        'residual': {
            'PM': array([0.]),
            'PM10': array([1.83502334]),
            'PM2.5': array([1.65168617]),
            'CO': array([11.79400365]),
            'CO2': array([132.71599523]),
            'CH4': array([0.63713447]),
            'NMHC': array([0.]),
            'NMOC': array([2.26025746]),
            'NH3': array([0.15417511]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.0903684]),
            'SO2': array([0.14509694])
        },
        'total': {
            'PM': array([0.]),
            'PM10': array([7.90932708]),
            'PM2.5': array([7.11910629]),
            'CO': array([50.03732961]),
            'CO2': array([682.99611045]),
            'CH4': array([2.56131097]),
            'NMHC': array([0.]),
            'NMOC': array([11.42680803]),
            'NH3': array([0.63766418]),
            'NO': array([0.]),
            'NO2': array([0.]),
            'NOX': array([0.57670624]),
            'SO2': array([0.65507066])
        }
    }

    EXPECTED_FIRE1_EMISSIONS_PM_ONLY = {
        'flaming': {
             'PM10': array([2.772095490888166]),
             'PM2.5': array([2.495135455344884])
        },
        'residual': {
            'PM10': array([1.8350233382047059]),
            'PM2.5': array([1.6516861730015355])
        },
        'smoldering': {
            'PM10': array([3.3022082538727515]),
            'PM2.5': array([2.9722846569511723])
        },
        'total': {
            'PM10': array([7.909327082965625]),
            'PM2.5': array([7.119106285297591])
        }
    }

    def test_wo_details(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(False, 'emissions', "include_emissions_details")
        set_old_consume_defaults()

        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')

        assert 'emissions_details' not in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])

    def test_with_details(self, reset_config):
        Config().set("consume", 'emissions', "model")
        Config().set(True, 'emissions', "include_emissions_details")
        set_old_consume_defaults()

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
        set_old_consume_defaults()

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
        set_old_consume_defaults()

        emissions.Consume(fire_failure_manager).run(self.fires)

        assert self.fires[0]['error'] == (
            'Missing fuelbed data required for computing emissions')
        assert 'emissions_details' in self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]
        self._check_emissions(self.EXPECTED_FIRE1_EMISSIONS_PM_ONLY,
            self.fires[1]['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]['emissions'])
