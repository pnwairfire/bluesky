"""Unit tests for bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import copy
from unittest import mock

from pytest import raises

from bluesky.config import Config
from bluesky.models.fires import Fire
from bluesky.modules import fuelbeds


##
## Tests for summarize
##

class TestSummarize():

    def test_no_fires(self):
        assert fuelbeds.summarize([]) == []

    def test_one_fire(self):
        fires = [
            Fire({
                'activity':[{
                    "active_areas":[{
                        "specified_points": [{
                            "area": 10,
                            "lat": 45,
                            "lng": -118,
                            "fuelbeds":[
                                {"fccs_id": "1", "pct": 40},
                                {"fccs_id": "2", "pct": 60}
                            ]
                        }]
                    }]
                }]
            })
        ]
        expected_summary = [
            {"fccs_id": "1", "pct": 40},
            {"fccs_id": "2", "pct": 60}
        ]
        summary = fuelbeds.summarize(fires)
        assert summary == expected_summary

    def test_two_fires(self):
        fires = [
            Fire({
                'activity':[{
                    "active_areas":[{
                        "specified_points": [{
                            "area": 10,
                            "lat": 45,
                            "lng": -118,
                            "fuelbeds":[
                                {"fccs_id": "1", "pct": 30},
                                {"fccs_id": "2", "pct": 70}
                            ]
                        }]
                    }]
                }]
            }),
            Fire({
                'activity':[{
                    "active_areas":[{
                        "specified_points": [{
                            "area": 5,
                            "lat": 44,
                            "lng": -117,
                            "fuelbeds":[
                                {"fccs_id": "2", "pct": 10},
                                {"fccs_id": "3", "pct": 90}
                            ]
                        }]
                    }]
                }]
            })
        ]
        expected_summary = [
            {"fccs_id": "1", "pct": 20},
            {"fccs_id": "2", "pct": 50},
            {"fccs_id": "3", "pct": 30}
        ]
        summary = fuelbeds.summarize(fires)
        assert summary == expected_summary

    # TODO: def test_two_fires_two_activity_each(self):
##
## Tests for Estimator.estimate
##

class TestEstimatorInsufficientDataForLookup():

    def setup_method(self):
        lookup = mock.Mock()
        self.estimator = fuelbeds.Estimator(lookup)

    def test_no_activity(self):
        with raises(ValueError) as e:
            self.estimator.estimate({})

    def test_no_location(self):
        with raises(ValueError) as e:
            self.estimator.estimate({'activity':[{}]})

    def test_no_geojson_or_lat_or_lng(self):
        with raises(ValueError) as e:
            self.estimator.estimate({"activity":[{"location":{}}]})


## Valid fuelbed info

FUELBED_INFO_60_40 = {
    "fuelbeds": {
        "46": {
            "grid_cells": 6, "percent": 60.0
        },
        "47": {
            "grid_cells": 4, "percent": 40.0
        }
    },
    "units": "m^2",
    "grid_cells": 5,
    "area": 4617927.854331356
}

FUELBED_INFO_24_12_48_12_4 = {
    "fuelbeds": {
        "46": {
            "grid_cells": 6, "percent": 24.0
        },
        "47": {
            "grid_cells": 3, "percent": 12.0
        },
        "48": {
            "grid_cells": 12, "percent": 48.0
        },
        "49": {
            "grid_cells": 3, "percent": 12.0
        },
        "50": {
            "grid_cells": 1, "percent": 4.0
        }
    },
    "units": "m^2",
    "grid_cells": 5,
    "area": 4617927.854331356
}

## Invalid fuelbed info

# total % < 100
FUELBED_INFO_60_30 = copy.deepcopy(FUELBED_INFO_60_40)
FUELBED_INFO_60_30['fuelbeds']['47']['percent'] = 30
# total % > 100
FUELBED_INFO_60_40_10 = copy.deepcopy(FUELBED_INFO_60_40)
FUELBED_INFO_60_40_10['fuelbeds']['50'] = {"grid_cells": 1, "percent": 10.0}

class BaseTestEstimatorEstimate():
    """Base class for testing Estimator.estimate
    """

    def setup_method(self):
        lookup = mock.Mock()
        self.estimator = fuelbeds.Estimator(lookup)

    # Tests of invalid lookup data

    def test_none_lookup_info(self):
        self.estimator.lookup.look_up = lambda p: None
        with raises(RuntimeError) as e:
            self.estimator.estimate(self.active_area_location)

    def test_empty_lookup_info(self):
        self.estimator.lookup.look_up = lambda p: {}
        with raises(RuntimeError) as e:
            self.estimator.estimate(self.active_area_location)

    def test_lookup_info_percentages_less_than_100(self):
        self.estimator.lookup.look_up = lambda p: FUELBED_INFO_60_30
        with raises(RuntimeError) as e:
            self.estimator.estimate(self.active_area_location)

    def test_lookup_info_percentages_greater_than_100(self):
        self.estimator.lookup.look_up = lambda p: FUELBED_INFO_60_40_10
        with raises(RuntimeError) as e:
            self.estimator.estimate(self.active_area_location)



class TestEstimatorGetFromPerimeter(BaseTestEstimatorEstimate):
    def setup_method(self):

        perimeter = {
            'geometry': {
                'type': 'Polygon',
                "coordinates": [
                    [
                        [-84.8194, 30.5222],
                        [-84.8197, 30.5209],
                        # ...add more coordinates...
                        [-84.8193, 30.5235],
                        [-84.8194, 30.5222]
                    ]
                ]
            }
        }
        self.active_area_location = perimeter
        super(TestEstimatorGetFromPerimeter, self).setup_method()

class TestEstimatorGetFromLatLng(BaseTestEstimatorEstimate):

    def setup_method(self):
        self.active_area_location = {"lat": 46.0, 'lng': -120.34}
        super(TestEstimatorGetFromLatLng, self).setup_method()

