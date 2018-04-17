"""Unit tests for hysplit_utils.

Run with py.test:
    > pip install pytest
    > py.test /path/to/hsyplit49/test/test_hysplit_utils.py
"""

import datetime
import time

from bluesky.dispersers.hysplit import hysplit_utils

class MockFireLocationData(object):
    def __init__(self, location_id):
        self.id = location_id

    def __repr__(self):
        return "<%s %d, location_id: %d>" % (self.__class__.__name__, id(self), self.id)
    # __str__ = __repr__

class TestHysplitUtils(object):

    def test_create_fire_sets(self):
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

    def test_create_fire_tranches(self):
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

    def test_compute_num_processes(self):
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

class TestKmPerLng(object):

    def test_basic(self):
        assert 111.32 == hysplit_utils.km_per_deg_lng(0)
        assert 78.71512688168647 == hysplit_utils.km_per_deg_lng(45)
        # Note: hysplit_utils.km_per_deg_lng(90) should equal 0
        #  using assert_approx_equal(0.0, hysplit_utils.km_per_deg_lng(90))
        #  fails, even thgouh the returned value is something like
        #  6.8163840840541674e-15.  So, just going to manually check
        #  that difference is insignificant
        assert hysplit_utils.km_per_deg_lng(90) < 0.000000000001

class TestSquareGridFromLatLng(object):

    def test_basic(self):
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


if __name__ == '__main__':
    test_main(verbose=True)
