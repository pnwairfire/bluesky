"""Unit tests for bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import copy
from unittest import mock

from numpy import array
from numpy.testing import assert_approx_equal
from py.test import raises

from bluesky.consumeutils import FuelLoadingsManager
from bluesky.models.fires import Fire
from bluesky.modules import consumption


fire = Fire({
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
                            "fuelbeds": [
                                {
                                    "fccs_id": "52",
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

def check_consumption(actual, expected):
    assert set(expected.keys()) == set(actual.keys())
    for c in expected:
        assert set(expected[c].keys()) == set(actual[c].keys())
        for s in expected[c]:
            assert set(expected[c][s].keys()) == set(actual[c][s].keys())
            for p in expected[c][s]:
                assert_approx_equal(actual[c][s][p][0], expected[c][s][p][0])

def foo(vals):
    for c in vals:
        for s in vals[c]:
            for p in vals[c][s]:
                vals[c][s][p] = list(vals[c][s][p])
    return vals

class TestConsumptionRunFire(object):

    def test(self):
        # TODO: create mock fuel loading manager class
        fuel_loadings_manager = FuelLoadingsManager()
        consumption._run_fire(fire, fuel_loadings_manager, 1)
        fb = fire['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]

        expected_heat = {
            'smoldering': [2412566576.4017043],
            'total': [6777717460.4055243],
            'residual': [1340653172.7602997],
            'flaming': [3024497711.2435193]
        }
        assert expected_heat == fb['heat']

        expected_consumption = {
            'canopy': {
                'ladder fuels': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'midstory': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'overstory': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'snags class 1 foliage': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'snags class 1 no foliage': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'snags class 1 wood': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'snags class 2': {'flaming': [0.0], 'residual': [0.0], 'smoldering': [0.0], 'total': [0.0]},
                'snags class 3': {'flaming': [0.0], 'residual': [0.0], 'smoldering': [0.0], 'total': [0.0]},
                'understory': {'flaming': [0.0],  'residual': [0.0],'smoldering': [0.0],'total': [0.0]}
            },
            'ground fuels': {
                'basal accumulations': {'flaming': [0.00045859784727272712],'residual': [0.0022929892363636353],'smoldering': [0.0018343913890909085], 'total': [0.0045859784727272706]},
                'duff lower': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                  'duff upper': {'flaming': [13.452203519999998],'residual': [26.904407039999995],'smoldering': [94.165424639999969],'total': [134.52203519999998]},
                  'squirrel middens': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]}
                },
            'litter-lichen-moss': {
            'lichen': {
                'flaming': [0.14868360324083274],'residual': [0.0],'smoldering': [0.007825452802149092],'total': [0.15650905604298185]},
                'litter': {'flaming': [50.821078916159998],'residual': [0.0],'smoldering': [5.6467865462399995],'total': [56.467865462399992]},
                'moss': {'flaming': [1.1665944254280725],'residual': [0.0],'smoldering': [0.061399706601477498],'total': [1.22799413202955]}
            },
            'nonwoody': {
                'primary live': {'flaming': [8.4133727999999994],'residual': [0.0],'smoldering': [0.93481920000000007],'total': [9.3481919999999992]},
                'secondary live': {'flaming': [0.42066864000000054],'residual': [0.0],'smoldering': [0.046740960000000061],'total': [0.46740960000000054]}
            },
            'shrub': {
                'primary live': {'flaming': [17.46396288],'residual': [0.0],'smoldering': [1.94044032],'total': [19.404403200000001]},
                'secondary live': {'flaming': [5.0504277600000016], 'residual': [0.0], 'smoldering': [0.56115864000000015], 'total': [5.6115864000000011]}
            },
            'summary': {
                'canopy': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                'ground fuels': {'flaming': [13.452662117847268], 'residual': [26.906700029236358], 'smoldering': [94.167259031389051], 'total': [134.52662117847271]},
                'litter-lichen-moss': {'flaming': [52.136356944828897],'residual': [0.0],'smoldering': [5.7160117056436262],'total': [57.852368650472521]},
                'nonwoody': {'flaming': [8.83404144], 'residual': [0.0],'smoldering': [0.98156016000000013],'total': [9.8156016000000008]},
                'shrub': {'flaming': [22.514390640000002],'residual': [0.0],'smoldering': [2.5015989599999999],'total': [25.015989600000001]},
                'total': {'flaming': [189.03110695271994],'residual': [83.790823297518727],'smoldering': [150.78541102510653],'total': [423.60734127534528]},
                'woody fuels': {'flaming': [92.093655810043785],'residual': [56.88412326828238],'smoldering': [47.418981168073863],'total': [196.39676024640005]}
            },
            'woody fuels': {
                '1-hr fuels': {'flaming': [16.219828799999998],'residual': [0.0],'smoldering': [0.85367520000000008],'total': [17.073504]},
                 '10-hr fuels': {'flaming': [34.573845600000006],'residual': [0.0],'smoldering': [3.8415384000000006],'total': [38.415384000000003]},
                 '100-hr fuels': {'flaming': [12.2128272],'residual': [0.71840160000000008],'smoldering': [1.4368032000000002],'total': [14.368031999999999]},
                 '1000-hr fuels rotten': {'flaming': [2.8541420126537145],'residual': [7.1353550316342869],'smoldering': [4.2812130189805719],'total': [14.270710063268574]},
                 '1000-hr fuels sound': {'flaming': [8.2870161230769241],'residual': [1.381169353846154],'smoldering': [4.1435080615384621],'total': [13.811693538461537]},
                 '10000-hr fuels rotten': {'flaming': [6.0119161543131447],'residual': [36.071496925878868],'smoldering': [18.035748462939434],'total': [60.11916154313144]},
                 '10000-hr fuels sound': {'flaming': [9.1157177353846173],'residual': [4.5578588676923086],'smoldering': [9.1157177353846173],'total': [22.789294338461541]},
                 '10k+-hr fuels rotten': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                 '10k+-hr fuels sound': {'flaming': [1.6574032246153847],'residual': [3.3148064492307694],'smoldering': [3.3148064492307694],'total': [8.2870161230769224]},
                 'piles': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                 'stumps lightered': {'flaming': [0.0],'residual': [0.0],'smoldering': [0.0],'total': [0.0]},
                 'stumps rotten': {'flaming': [0.61750584000000008],'residual': [3.7050350399999998],'smoldering': [1.8525175199999999],'total': [6.1750584000000002]},
                 'stumps sound': {'flaming': [0.54345312000000001],'residual': [0.0],'smoldering': [0.54345312000000001],'total': [1.08690624]}
            }
        }

        check_consumption(fb['consumption'], expected_consumption)
