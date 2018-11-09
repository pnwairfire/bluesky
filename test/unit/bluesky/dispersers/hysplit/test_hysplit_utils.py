"""Unit tests for hysplit_utils.

Run with py.test:
    > pip install pytest
    > py.test /path/to/hsyplit49/test/test_hysplit_utils.py
"""

import datetime
import time

from py.test import raises

from bluesky.dispersers.hysplit import hysplit_utils
from bluesky.exceptions import BlueSkyConfigurationError

class MockFireLocationData(object):
    def __init__(self, location_id):
        self.id = location_id

    def __repr__(self):
        return "<%s %d, location_id: %d>" % (self.__class__.__name__, id(self), self.id)
    # __str__ = __repr__

class TestCreateFireSets(object):

    def test(self):
        fires = [
            MockFireLocationData(1),
            MockFireLocationData(2),
            MockFireLocationData(1),
            MockFireLocationData(4),
            MockFireLocationData(4),
            MockFireLocationData(100),
            MockFireLocationData(3),
            MockFireLocationData(1),
            MockFireLocationData(1)
        ]
        expected_sets = [
            [fires[0], fires[2], fires[7], fires[8]],  # id 1
            [fires[1]],  # id 2
            [fires[6]],  # id 3
            [fires[3], fires[4]],  # id 4
            [fires[5]]  #id 100
        ]
        fire_sets = hysplit_utils.create_fire_sets(fires)
        # order not preserved, so sort results
        assert expected_sets == sorted(fire_sets, key=lambda e: e[0].id)


class TestCreateFireTranches(object):

    def test(self):
        fire_sets = [
            [MockFireLocationData(1), MockFireLocationData(1)],
            [MockFireLocationData(3), MockFireLocationData(3)],
            [MockFireLocationData(7), MockFireLocationData(7)],
            [MockFireLocationData(22), MockFireLocationData(22)]
        ]

        # 4 fires locations, 5 proceses  <-- should assume only 4 processes
        expected_tranches = [
            [fire_sets[0][0], fire_sets[0][1]],
            [fire_sets[1][0], fire_sets[1][1]],
            [fire_sets[2][0], fire_sets[2][1]],
            [fire_sets[3][0], fire_sets[3][1]]
        ]
        fire_tranches = hysplit_utils.create_fire_tranches(fire_sets, 5)
        assert expected_tranches == fire_tranches

        # 4 fires locations, 4 proceses  <-- same expected set as when called with num_processes = 5
        fire_tranches = hysplit_utils.create_fire_tranches(fire_sets, 4)
        assert expected_tranches == fire_tranches

        # 4 fires locations, 3 proceses
        expected_tranches = [
            [fire_sets[0][0], fire_sets[0][1],
             fire_sets[1][0], fire_sets[1][1]],
            [fire_sets[2][0], fire_sets[2][1]],
            [fire_sets[3][0], fire_sets[3][1]]
        ]
        fire_tranches = hysplit_utils.create_fire_tranches(fire_sets, 3)
        assert expected_tranches == fire_tranches

        # 4 fires locations, 2 proceses
        expected_tranches = [
            [fire_sets[0][0], fire_sets[0][1],
             fire_sets[1][0], fire_sets[1][1]],
            [fire_sets[2][0], fire_sets[2][1],
             fire_sets[3][0], fire_sets[3][1]]
        ]
        fire_tranches = hysplit_utils.create_fire_tranches(fire_sets, 2)
        assert expected_tranches == fire_tranches

        # 4 fires locations, 1 proceses
        expected_tranches = [
            [fire_sets[0][0], fire_sets[0][1],
             fire_sets[1][0], fire_sets[1][1],
             fire_sets[2][0], fire_sets[2][1],
             fire_sets[3][0], fire_sets[3][1]]
        ]
        fire_tranches = hysplit_utils.create_fire_tranches(fire_sets, 1)
        assert expected_tranches == fire_tranches


class TestComputeNumProcesses(object):

    def test(self):
        n = hysplit_utils.compute_num_processes(4)
        assert isinstance(n, int) and n == 1

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=0, num_processes_max=0)
        assert isinstance(n, int) and n == 1

        n = hysplit_utils.compute_num_processes(4, num_processes=1,
            num_fires_per_process=0, num_processes_max=0)
        assert isinstance(n, int) and n == 1

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=1, num_processes_max=3)
        assert isinstance(n, int) and n == 3

        n = hysplit_utils.compute_num_processes(6, num_processes=0,
            num_fires_per_process=2, num_processes_max=4)
        assert isinstance(n, int) and n == 3

        n = hysplit_utils.compute_num_processes(4, num_processes=2,
            num_fires_per_process=1, num_processes_max=3)
        assert isinstance(n, int) and n == 2

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=2, num_processes_max=3)
        assert isinstance(n, int) and n == 2

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=2, num_processes_max=1)
        assert isinstance(n, int) and n == 1

    def test_with_parinit(self):
        n = hysplit_utils.compute_num_processes(4,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 1

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=0, num_processes_max=0,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 1

        n = hysplit_utils.compute_num_processes(4, num_processes=1,
            num_fires_per_process=0, num_processes_max=0,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 1

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=1, num_processes_max=3,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 3

        n = hysplit_utils.compute_num_processes(6, num_processes=0,
            num_fires_per_process=2, num_processes_max=4,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 4

        n = hysplit_utils.compute_num_processes(4, num_processes=2,
            num_fires_per_process=1, num_processes_max=3,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 3

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=2, num_processes_max=3,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 3

        n = hysplit_utils.compute_num_processes(4, num_processes=0,
            num_fires_per_process=2, num_processes_max=1,
            parinit_or_pardump=True)
        assert isinstance(n, int) and n == 1


class TestKmPerLng(object):

    def test(self):
        assert 111.32 == hysplit_utils.km_per_deg_lng(0)
        assert 78.71512688168647 == hysplit_utils.km_per_deg_lng(45)
        # Note: hysplit_utils.km_per_deg_lng(90) should equal 0
        #  using assert_approx_equal(0.0, hysplit_utils.km_per_deg_lng(90))
        #  fails, even thgouh the returned value is something like
        #  6.8163840840541674e-15.  So, just going to manually check
        #  that difference is insignificant
        assert hysplit_utils.km_per_deg_lng(90) < 0.000000000001

class TestSquareGridFromLatLng(object):

    def test(self):
        e = {
            "center_latitude": 45.0,
            "center_longitude": -118.0,
            "height_latitude": 0.9009009009009009,
            "width_longitude": 1.2704038469036067,
            "spacing_longitude": 0.0762242308142164,
            "spacing_latitude": 0.05405405405405406
        }
        assert e == hysplit_utils.square_grid_from_lat_lng(
            45.0, -118.0, 6.0, 6.0, 100, input_spacing_in_degrees=False)

        # lat/lon projection
        e = {
            "center_latitude": 45.0,
            "center_longitude": -118.0,
            "height_latitude": 0.9009009009009009,
            "width_longitude": 1.2704038469036067,
            "spacing_longitude": 0.05,
            "spacing_latitude": 0.05
        }
        assert e == hysplit_utils.square_grid_from_lat_lng(
            45.0, -118.0, 0.05, 0.05, 100, input_spacing_in_degrees=True)

    # TODO: test location that could cross pole
    # TODO: test location that could equator
    # TODO: test any invalid cases

class TestGridParamsFromGrid(object):

    def test_llc_projection(self):
        grid = {
            "spacing": 6.0,
            #"projection": 'LLC',
            "boundary": {
                "ne": {
                    "lat": 45.25,
                    "lng": -106.5
                },
                "sw": {
                    "lat": 27.75,
                    "lng": -131.5
                }
            }
        }

        # 0.06705008458604998 == 6.0 / (111.32 * math.cos(math.pi / 180.0 * 36.5))
        spacing = 0.06705008458604998
        expected = {
            "spacing_latitude": spacing,
            "spacing_longitude": spacing,
            "center_latitude": 36.5,
            "center_longitude": -119.0,
            "height_latitude": 17.5,
            "width_longitude": 25.0
        }
        assert expected == hysplit_utils.grid_params_from_grid(grid)

    def test_latlong_projection(self):
        grid = {
            "spacing": 0.06,
            "projection": "LatLon",
            "boundary": {
                "ne": {
                    "lat": 45.25,
                    "lng": -106.5
                },
                "sw": {
                    "lat": 27.75,
                    "lng": -131.5
                }
            }
        }
        expected = {
            "spacing_latitude": 0.06,
            "spacing_longitude": 0.06,
            "center_latitude": 36.5,
            "center_longitude": -119.0,
            "height_latitude": 17.5,
            "width_longitude": 25.0
        }
        assert expected == hysplit_utils.grid_params_from_grid(grid)

class TestGetGridParams(object):

    def test_user_defined_grid(self):
        config = {
            "USER_DEFINED_GRID": True,
            "CENTER_LATITUDE": 36.5,
            "CENTER_LONGITUDE": -119.0,
            "WIDTH_LONGITUDE": 25.0,
            "HEIGHT_LATITUDE": 17.5,
            "SPACING_LONGITUDE": 0.05,
            "SPACING_LATITUDE": 0.05
        }
        expected = {
            'center_latitude': 36.5,
            'center_longitude': -119.0,
            'height_latitude': 17.5,
            'spacing_latitude': 0.05,
            'spacing_longitude': 0.05,
            'width_longitude': 25.0
        }
        assert expected == hysplit_utils.get_grid_params(config)

    def test_grid(self):
        config = {
            "grid": {
                "spacing": 6.0,
                "boundary": {
                    "ne": {
                        "lat": 45.25,
                        "lng": -106.5
                    },
                    "sw": {
                        "lat": 27.75,
                        "lng": -131.5
                    }
                }
            }
        }
        expected = {
            'center_latitude': 36.5,
            'center_longitude': -119.0,
            'height_latitude': 17.5,
            'spacing_latitude': 0.06705008458604998,
            'spacing_longitude': 0.06705008458604998,
            'width_longitude': 25.0
        }
        assert expected == hysplit_utils.get_grid_params(config)

    def test_compute_grid(self):
        fires_one = [{'latitude': 40.0, 'longitude': -118.5}]
        fires_two = [
            {'latitude': 40.0, 'longitude': -118.5},
            {'latitude': 45.0, 'longitude': -117.5}
        ]
        config = {
            "compute_grid": True,
        }

        ## Missing spacing

        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(config, fires=fires_one)
        assert e_info.value.args[0] == ("Config settings 'spacing_latitude' "
                "and 'spacing_longitude' required to compute hysplit grid")
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(
                dict(config, spacing_longitude=0.05), fires=fires_one)
        assert e_info.value.args[0] == ("Config settings 'spacing_latitude' "
                "and 'spacing_longitude' required to compute hysplit grid")
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(
                dict(config, spacing_latitude=0.05), fires=fires_one)
        assert e_info.value.args[0] == ("Config settings 'spacing_latitude' "
                "and 'spacing_longitude' required to compute hysplit grid")


        ## no fires or two many fires

        config.update(spacing_longitude=0.05, spacing_latitude=0.05)

        with raises(ValueError) as e_info:
            hysplit_utils.get_grid_params(config)
        assert e_info.value.args[0] == 'Option to compute grid only supported for runs with one fire'

        with raises(ValueError) as e_info:
            hysplit_utils.get_grid_params(config, fires=fires_two)
        assert e_info.value.args[0] == 'Option to compute grid only supported for runs with one fire'

        ## successful cases

        expected = {
            'center_latitude': 40.0,
            'center_longitude': -118.5,
            'height_latitude': 18.01801801801802,
            'spacing_latitude': 0.05,
            'spacing_longitude': 0.05,
            'width_longitude': 23.45323911843835
        }
        assert expected == hysplit_utils.get_grid_params(config, fires=fires_one)

        # custom grid length (default is 2000)
        config['grid_length'] = 1000
        expected = {
            'center_latitude': 40.0,
            'center_longitude': -118.5,
            'height_latitude': 9.00900900900901,
            'spacing_latitude': 0.05,
            'spacing_longitude': 0.05,
            'width_longitude': 11.726619559219175
        }
        assert expected == hysplit_utils.get_grid_params(config, fires=fires_one)

    def test_met_info(self):
        config = {}
        met_info = {
            "grid": {
                "spacing": 6.0,
                "boundary": {
                    "ne": {
                        "lat": 45.25,
                        "lng": -106.5
                    },
                    "sw": {
                        "lat": 27.75,
                        "lng": -131.5
                    }
                }
            }
        }
        expected = {
            'center_latitude': 36.5,
            'center_longitude': -119.0,
            'height_latitude': 17.5,
            'spacing_latitude': 0.06705008458604998,
            'spacing_longitude': 0.06705008458604998,
            'width_longitude': 25.0
        }
        assert expected == hysplit_utils.get_grid_params(
            config, met_info=met_info)

    def test_allow_undefined(self):
        config = {}
        expected = {}
        assert expected == hysplit_utils.get_grid_params(
            config, allow_undefined=True)

    def test_fail(self):
        config = {}
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(config)
        assert e_info.value.args[0] == 'Specify hysplit dispersion grid'
