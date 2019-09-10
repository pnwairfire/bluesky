"""Unit tests for bluesky.modules.fuelbeds"""

__author__ = "Joel Dubowy"

import copy
from unittest import mock

from py.test import raises

from bluesky.config import Config
from bluesky.models.fires import Fire
from bluesky.modules import fuelbeds


##
## Tests for summarize
##

class TestSummarize(object):

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

class TestEstimatorInsufficientDataForLookup(object):

    def setup(self):
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

class BaseTestEstimatorEstimate(object):
    """Base class for testing Estimator.estimate
    """

    def setup(self):
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

    # Test of valid lookup data

    def test_no_truncation(self):
        self.estimator.lookup.look_up = lambda p: FUELBED_INFO_60_40
        expected_fuelbeds = [
            {'fccs_id': '46', 'pct': 60},
            {'fccs_id': '47', 'pct': 40}
        ]
        # Having 'geojson' key will trigger call to self.estimator.lookup.look_up;
        # The value of GeoJSON is not actually used here
        self.estimator.estimate(self.active_area_location)
        assert expected_fuelbeds == self.active_area_location.get('fuelbeds')
        assert 100.0 == self.active_area_location.get('fuelbeds_total_accounted_for_pct')

    def test_with_truncation(self):
        self.estimator.lookup.look_up = lambda p: FUELBED_INFO_24_12_48_12_4
        expected_fuelbeds = [
            {'fccs_id': "48", 'pct': 50.0},
            {'fccs_id': "46", 'pct': 25.0},
            {'fccs_id': "47", 'pct': 12.5},
            {'fccs_id': "49", 'pct': 12.5}
        ]
        # Having 'geojson' key will trigger call to self.estimator.lookup.look_up;
        # The value of GeoJSON is not actually used here
        self.estimator.estimate(self.active_area_location)
        assert expected_fuelbeds == self.active_area_location.get('fuelbeds')
        assert 96.0 == self.active_area_location.get('fuelbeds_total_accounted_for_pct')

class TestEstimatorGetFromPerimeter(BaseTestEstimatorEstimate):
    def setup(self):

        perimeter = {
            "polygon": [
                [-84.8194, 30.5222],
                [-84.8197, 30.5209],
                # ...add more coordinates...
                [-84.8193, 30.5235],
                [-84.8194, 30.5222]
            ]
        }
        self.active_area_location = perimeter
        super(TestEstimatorGetFromPerimeter, self).setup()

class TestEstimatorGetFromLatLng(BaseTestEstimatorEstimate):

    def setup(self):
        self.active_area_location = {"lat": 46.0, 'lng': -120.34}
        super(TestEstimatorGetFromLatLng, self).setup()

##
## Tests for Estimator._truncate
##

class TestEstimatorDefaultTruncation(object):

    def setup(self):
        lookup = mock.Mock()
        self.estimator = fuelbeds.Estimator(lookup)

    def test_truncate_empty_set(self):
        expected = {
            "fuelbeds_total_accounted_for_pct": 0.0,
            "fuelbeds": []
        }
        actual = self.estimator._truncate([])
        assert expected == actual

    def test_truncate_one_fuelbed(self):
        # w/ truncation config defaults
        actual = self.estimator._truncate(
            [{'fccs_id': 1, 'pct': 100}])
        expected = {
            "fuelbeds_total_accounted_for_pct": 100,
            "fuelbeds": [{'fccs_id': 1, 'pct': 100}]
        }
        assert expected == actual

        # a single fuelbed's percentage should never be below 100%,
        # let alone the truncation percemtage threshold, but code
        # should handle it
        # w/ truncation config defaults
        pct = self.estimator.percentage_threshold - 1
        actual = self.estimator._truncate(
            [{'fccs_id': 1, 'pct': pct}])
        expected = {
            "fuelbeds_total_accounted_for_pct": pct,
            "fuelbeds": [{'fccs_id': 1, 'pct': 100.0}]
        }
        assert expected == actual


    def test_truncate_multiple_fbs_no_truncation(self):
        # w/ truncation config defaults
        input_fuelbeds = [
            {'fccs_id': 1, 'pct': 50},
            {'fccs_id': 2, 'pct': 20},
            {'fccs_id': 3, 'pct': 30}
        ]
        actual = self.estimator._truncate(input_fuelbeds)
        expected =  {
            "fuelbeds_total_accounted_for_pct": 100,
            "fuelbeds": [
                {'fccs_id': 1, 'pct': 50},
                {'fccs_id': 3, 'pct': 30},
                {'fccs_id': 2, 'pct': 20}
            ]
        }
        assert expected == actual

    def test_truncate_multiple_fbs_truncated(self):
        # w/ truncation config defaults - percent threshold comes into play
        input_fuelbeds = [
            {'fccs_id': 3, 'pct': 23},
            {'fccs_id': 1, 'pct': 69},
            {'fccs_id': 2, 'pct': 8}
        ]
        actual = self.estimator._truncate(input_fuelbeds)
        expected = {
            "fuelbeds_total_accounted_for_pct": 92.0,
            "fuelbeds": [
                {'fccs_id': 1, 'pct': 75},
                {'fccs_id': 3, 'pct': 25}
            ]
        }
        assert expected == actual

        input_fuelbeds = [
            {'fccs_id': 5, 'pct': 24},
            {'fccs_id': 45, 'pct': 12},
            {'fccs_id': 1, 'pct': 48},
            {'fccs_id': 223, 'pct': 12},
            {'fccs_id': 3, 'pct': 4}
        ]
        actual = self.estimator._truncate(input_fuelbeds)
        expected = {
            "fuelbeds_total_accounted_for_pct": 96,
            "fuelbeds": [
                {'fccs_id': 1, 'pct': 50.0},
                {'fccs_id': 5, 'pct': 25.0},
                {'fccs_id': 45, 'pct': 12.5},
                {'fccs_id': 223, 'pct': 12.5}
            ]
        }
        assert expected == actual

        # w/ truncation config defaults - count threshold comes into play
        input_fuelbeds = [
            {'fccs_id': 5, 'pct': 13.2},
            {'fccs_id': 323, 'pct': 35.2},
            {'fccs_id': 3, 'pct': 4},
            {'fccs_id': 1, 'pct': 17.6},
            {'fccs_id': 223, 'pct': 13.2},
            {'fccs_id': 98, 'pct': 8.8},
            {'fccs_id': 145, 'pct': 8}
        ]
        actual = self.estimator._truncate(input_fuelbeds)
        expected = {
            "fuelbeds_total_accounted_for_pct": 88.0,
            "fuelbeds": [
                {'fccs_id': 323, 'pct': 40.0},
                {'fccs_id': 1, 'pct': 20.0},
                {'fccs_id': 5, 'pct': 15.0},
                {'fccs_id': 223, 'pct': 15.0},
                {'fccs_id': 98, 'pct': 10.0},
            ]
        }
        assert expected == actual


class TestEstimatorCustomTruncation(object):

    def setup(self):
        lookup = mock.Mock()
        Config().set(75.0, "fuelbeds", "truncation_percentage_threshold")
        Config().set(2, "fuelbeds", "truncation_count_threshold")
        self.estimator_w_options = fuelbeds.Estimator(lookup)

    def test_truncate_empty_set(self):
        expected = {
            "fuelbeds_total_accounted_for_pct": 0.0,
            "fuelbeds": []
        }
        actual = self.estimator_w_options._truncate([])
        assert expected == actual

    def test_truncate_one_fuelbed(self):
        # with custom truncation options (which don't come into play here)
        actual = self.estimator_w_options._truncate(
            [{'fccs_id': 1, 'pct': 100.0}])
        expected = {
            "fuelbeds_total_accounted_for_pct": 100.0,
            "fuelbeds": [{'fccs_id': 1, 'pct': 100.0}]
        }
        assert expected == actual

        # a single fuelbed's percentage should never be below 100%,
        # let alone the truncation percemtage threshold, but code
        # should handle it
        # with custom truncation options (which don't come into play here)
        pct = self.estimator_w_options.percentage_threshold - 1
        actual = self.estimator_w_options._truncate(
            [{'fccs_id': 1, 'pct': pct}])
        expected = {
            "fuelbeds_total_accounted_for_pct": pct,
            "fuelbeds": [{'fccs_id': 1, 'pct': 100.0}]
        }
        assert expected == actual


    def test_truncate_multiple_fbs_no_truncation(self):
        # with custom truncation options (which don't come into play here)
        input_fuelbeds = [
            {'fccs_id': 1, 'pct': 60.0},
            {'fccs_id': 2, 'pct': 40.0}
        ]
        actual = self.estimator_w_options._truncate(input_fuelbeds)
        expected =  {
            "fuelbeds_total_accounted_for_pct": 100.0,
            "fuelbeds": [
                {'fccs_id': 1, 'pct': 60.0},
                {'fccs_id': 2, 'pct': 40.0}
            ]
        }
        assert expected == actual

    def test_truncate_multiple_fbs_truncated(self):
        # with custom truncation options - percent threshold comes into play
        input_fuelbeds = [
            {'fccs_id': 5, 'pct': 76.0},
            {'fccs_id': 323, 'pct': 24.0}
        ]
        actual = self.estimator_w_options._truncate(input_fuelbeds)
        expected = {
            "fuelbeds_total_accounted_for_pct": 76.0,
            "fuelbeds": [
                {'fccs_id': 5, 'pct': 100.0}
            ]
        }
        assert expected == actual
        # with custom truncation options - count threshold comes into play
        input_fuelbeds = [
            {'fccs_id': 5, 'pct': 42.0},
            {'fccs_id': 123, 'pct': 20.0},
            {'fccs_id': 323, 'pct': 28.0},
            {'fccs_id': 1, 'pct': 10.0}
        ]
        actual = self.estimator_w_options._truncate(input_fuelbeds)
        expected = {
            "fuelbeds_total_accounted_for_pct": 70.0,
            "fuelbeds": [
                {'fccs_id': 5, 'pct': 60.0},
                {'fccs_id': 323, 'pct': 40.0}
            ]
        }
        assert expected == actual




class TestEstimatorNoTruncation(object):

    def setup(self):
        lookup = mock.Mock()
        Config().set(None, "fuelbeds", "truncation_percentage_threshold")
        Config().set(None, "fuelbeds", "truncation_count_threshold")
        self.estimator_no_truncation = fuelbeds.Estimator(lookup)


    # TDOO: UPDATE ALL THESE TESTS TO USE NEW CLASS INTERFACE


    def test_truncate_empty_set(self):
        expected = {
            "fuelbeds_total_accounted_for_pct": 0.0,
            "fuelbeds": []
        }
        actual = self.estimator_no_truncation._truncate([])
        assert expected == actual

    def test_truncate_one_fuelbed(self):


        # with truncation turned off
        actual = self.estimator_no_truncation._truncate(
            [{'fccs_id': 1, 'pct': 100.0}])
        expected = {
            "fuelbeds_total_accounted_for_pct": 100.0,
            "fuelbeds": [{'fccs_id': 1, 'pct': 100.0}]
        }

        # a single fuelbed's percentage should never be below 100%,
        # but code should handle it
        # with truncation turned off
        actual = self.estimator_no_truncation._truncate(
            [{'fccs_id': 1, 'pct': 76.0}])
        expected = {
            "fuelbeds_total_accounted_for_pct": 76.0,
            "fuelbeds": [{'fccs_id': 1, 'pct': 100.0}]
        }

    def test_truncate_multiple_fbs_no_truncation(self):
        # with truncation turned off
        input_fuelbeds = [
            {'fccs_id': 1, 'pct': 60.0},
            {'fccs_id': 2, 'pct': 40.0}
        ]
        actual = self.estimator_no_truncation._truncate(input_fuelbeds)
        expected =  {
            "fuelbeds_total_accounted_for_pct": 100.0,
            "fuelbeds": [
                {'fccs_id': 1, 'pct': 60.0},
                {'fccs_id': 2, 'pct': 40.0}
            ]
        }
        assert expected == actual

        input_fuelbeds = [
            {'fccs_id': 5, 'pct': 13.2},
            {'fccs_id': 323, 'pct': 35.2},
            {'fccs_id': 3, 'pct': 4.0},
            {'fccs_id': 1, 'pct': 17.6},
            {'fccs_id': 223, 'pct': 13.2},
            {'fccs_id': 98, 'pct': 8.8},
            {'fccs_id': 145, 'pct': 8.0}
        ]
        actual = self.estimator_no_truncation._truncate(input_fuelbeds)
        expected = {
            "fuelbeds_total_accounted_for_pct": 100.0,
            "fuelbeds": [
                {'fccs_id': 323, 'pct': 35.2},
                {'fccs_id': 1, 'pct': 17.6},
                {'fccs_id': 5, 'pct': 13.2},
                {'fccs_id': 223, 'pct': 13.2},
                {'fccs_id': 98, 'pct': 8.8},
                {'fccs_id': 145, 'pct': 8.0},
                {'fccs_id': 3, 'pct': 4.0}
            ]
        }
        assert expected == actual


    # Note: test_truncate_multiple_fbs_truncated not defined for
    #   estimator with truncation turned off

# ##
# ## Tests for Estimator._adjust_percentages
# ##

class TestEstimatorPercentageAdjustment(object):

    def setup(self):
        lookup = mock.Mock()
        self.estimator = fuelbeds.Estimator(lookup)

    def test_no_adjustment(self):
        input_fuelbeds = [
            {'fccs_id': 1, 'pct': 60},
            {'fccs_id': 3, 'pct': 40}
        ]
        actual = self.estimator._adjust_percentages(input_fuelbeds)
        expected = [
            {'fccs_id': 1, 'pct': 60},
            {'fccs_id': 3, 'pct': 40}
        ]
        assert expected == actual

    def test_with_adjustment(self):
        input_fuelbeds = [
            {'fccs_id': 5, 'pct': 42.0},
            {'fccs_id': 323, 'pct': 28.0}
        ]
        actual = self.estimator._adjust_percentages(input_fuelbeds)
        expected = [
            {'fccs_id': 5, 'pct': 60.0},
            {'fccs_id': 323, 'pct': 40.0}
        ]
        assert expected == actual
