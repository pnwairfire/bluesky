"""Unit tests for bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

import copy
from unittest import mock

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
                    "utc_offset": "-07:00",
                    "ecoregion": "western",
                    'slope': 5,
                    'windspeed': 5,
                    'rain_days': 10,
                    'moisture_10hr': 50,
                    'length_of_ignition': 120,
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

class TestConsumptionRunFire(object):

    def test(self):
        # TODO: create mock fuel loading manager class
        fuel_loadings_manager = FuelLoadingsManager()
        consumption._run_fire(fire, fuel_loadings_manager, 1)
        fb = fire['activity'][0]['active_areas'][0]['specified_points'][0]['fuelbeds'][0]

        # TODO: make sure the following, commented out heat is correct
        expected_heat = {
            # 'flaming': array([  3.04787217e+09]),
            # 'residual': array([  1.37547756e+09]),
            # 'smoldering': array([  1.99089601e+09]),
            # 'total': array([  6.41424574e+09])
        }
        #assert expected_heat == fb['heat']

        #expected_consumption = {}
