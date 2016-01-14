"""Unit tests for bluesky.modules.timeprofiling"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import copy
#from py.test import raises

from bluesky.modules import timeprofiling

class TestScaleEmissions(object):

    def test_deep_nested(self):
        d = {
            "canopy": {
                "ladder fuels": {
                    "flaming": {
                        "CH4": [0.4],
                        "VOC": [1.2]
                    },
                    "residual": {
                        "CH4": [0.0],
                        "CO": [2.0]
                    }
                }
            }
        }
        not_scaled = copy.deepcopy(d)
        scaled = {
            "canopy": {
                "ladder fuels": {
                    "flaming": {
                        "CH4": [0.1],
                        "VOC": [0.3]
                    },
                    "residual": {
                        "CH4": [0.0],
                        "CO": [0.5]
                    }
                }
            }
        }

        timeprofiling._scale_emissions(d, 100.0)
        assert d == not_scaled
        assert d != scaled
        timeprofiling._scale_emissions(d, 25.0)
        assert d == scaled

    def test_nested(self):
        d = {
            "flaming": {
                "CH4": [0.4],
                "VOC": [1.2]
            },
            "residual": {
                "CH4": [0.0],
                "CO": [2.0]
            }
        }
        not_scaled = copy.deepcopy(d)
        scaled = {
            "flaming": {
                "CH4": [0.1],
                "VOC": [0.3]
            },
            "residual": {
                "CH4": [0.0],
                "CO": [0.5]
            }
        }

        timeprofiling._scale_emissions(d, 100.0)
        assert d == not_scaled
        assert d != scaled
        timeprofiling._scale_emissions(d, 25.0)
        assert d == scaled

    def test_not_ested(self):
        d = {"CH4": [0.4]}
        not_scaled = copy.deepcopy(d)
        scaled = {"CH4": [0.1]}
        timeprofiling._scale_emissions(d, 100.0)
        assert d == not_scaled
        assert d != scaled
        timeprofiling._scale_emissions(d, 25.0)
        assert d == scaled
