"""Unit tests for bluesky.dispersers.hysplit.hysplit_utils
"""

import copy
import datetime
import time

from py.test import raises
from numpy.testing import assert_approx_equal

from bluesky.config import Config
from bluesky.dispersers.hysplit import hysplit_utils
from bluesky.exceptions import BlueSkyConfigurationError

class MockFireLocationData(object):
    def __init__(self, location_id):
        self.id = location_id

    def __repr__(self):
        return "<%s %d, location_id: %d>" % (self.__class__.__name__, id(self), self.id)
    # __str__ = __repr__


##
## Tranching
##

class TestCreateFireSets(object):

    def test(self, reset_config):
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
            [fires[0]],
            [fires[2]],
            [fires[7]],
            [fires[8]],
            [fires[1]],
            [fires[6]],
            [fires[3]],
            [fires[4]],
            [fires[5]]
        ]
        fire_sets = hysplit_utils.create_fire_sets(fires)
        # order not preserved, so sort results
        assert expected_sets == sorted(fire_sets, key=lambda e: e[0].id)


class TestCreateFireTranches(object):

    def test(self, reset_config):
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

    def test(self, reset_config):
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

    def test_with_parinit(self, reset_config):
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

##
## Dummy Fires
##

class TestDummyTimeprofiledEmissionsHour(object):

    def test_one_hour(self, reset_config):
        expected = {
            "pm2.5": 0.0, "pm10": 0.0, "co": 0.0,
            "co2": 0.0, "ch4": 0.0, "nox": 0.0,
            "nh3": 0.0, "so2": 0.0, "voc": 0.0,
            "pm": 0.0, "nmhc": 0.0
        }
        assert expected == hysplit_utils.dummy_timeprofiled_emissions_hour()

class TestGenerateDummyFire(object):

    EXPECTED_PLUMERISE_HOUR = {
        'emission_fractions': [
            0.05, 0.05, 0.05, 0.05, 0.05,
            0.05, 0.05, 0.05, 0.05, 0.05,
            0.05, 0.05, 0.05, 0.05, 0.05,
            0.05, 0.05, 0.05, 0.05, 0.05
        ],
        'heights': [
            1000,1100,1200,1300,1400,
            1500,1600,1700,1800,1900,
            2000,2100,2200,2300,2400,
            2500,2600,2700,2800,2900,
            3000
        ],
        'smolder_fraction': 0.0
    }

    def test_one_hour(self, reset_config):
        expected = {
            "is_dummy": True,
            "area": 1,
            "type": "wildfire",
            "fuel_type": "natural",
            "latitude": 40,
            "longitude": -110,
            "utc_offset": 0,
            "plumerise": {
                "2018-11-09T00:00:00": self.EXPECTED_PLUMERISE_HOUR
            },
            "timeprofiled_area": {
                "2018-11-09T00:00:00": 1.0,
            },
            "timeprofiled_emissions": {
                "2018-11-09T00:00:00": {
                    "pm2.5": 0.0, "pm10": 0.0, "co": 0.0,
                    "co2": 0.0, "ch4": 0.0, "nox": 0.0,
                    "nh3": 0.0, "so2": 0.0, "voc": 0.0,
                    "pm": 0.0, "nmhc": 0.0
                }
            }
        }
        f = hysplit_utils.generate_dummy_fire(
            datetime.datetime(2018,11,9), 1,
            {"center_latitude": 40, "center_longitude": -110}
        )
        expected["id"] = f["id"] # id is randomly generated
        assert expected == f

    def test_four_hours(self, reset_config):
        expected = {
            "is_dummy": True,
            "area": 1,
            "type": "wildfire",
            "fuel_type": "natural",
            "latitude": 40,
            "longitude": -110,
            "utc_offset": 0,
            "plumerise": {
                "2018-11-09T00:00:00": self.EXPECTED_PLUMERISE_HOUR,
                "2018-11-09T01:00:00": self.EXPECTED_PLUMERISE_HOUR,
                "2018-11-09T02:00:00": self.EXPECTED_PLUMERISE_HOUR,
                "2018-11-09T03:00:00": self.EXPECTED_PLUMERISE_HOUR

            },
            "timeprofiled_area": {
                "2018-11-09T00:00:00": 0.25,
                "2018-11-09T01:00:00": 0.25,
                "2018-11-09T02:00:00": 0.25,
                "2018-11-09T03:00:00": 0.25
            },
            "timeprofiled_emissions": {
                "2018-11-09T00:00:00":{
                    "pm2.5": 0.0, "pm10": 0.0, "co": 0.0,
                    "co2": 0.0, "ch4": 0.0, "nox": 0.0,
                    "nh3": 0.0, "so2": 0.0, "voc": 0.0,
                    "pm": 0.0, "nmhc": 0.0
                },
                "2018-11-09T01:00:00":{
                    "pm2.5": 0.0, "pm10": 0.0, "co": 0.0,
                    "co2": 0.0, "ch4": 0.0, "nox": 0.0,
                    "nh3": 0.0, "so2": 0.0, "voc": 0.0,
                    "pm": 0.0, "nmhc": 0.0
                },
                "2018-11-09T02:00:00":{
                    "pm2.5": 0.0, "pm10": 0.0, "co": 0.0,
                    "co2": 0.0, "ch4": 0.0, "nox": 0.0,
                    "nh3": 0.0, "so2": 0.0, "voc": 0.0,
                    "pm": 0.0, "nmhc": 0.0
                },
                "2018-11-09T03:00:00":{
                    "pm2.5": 0.0, "pm10": 0.0, "co": 0.0,
                    "co2": 0.0, "ch4": 0.0, "nox": 0.0,
                    "nh3": 0.0, "so2": 0.0, "voc": 0.0,
                    "pm": 0.0, "nmhc": 0.0
                }
            }
        }
        f = hysplit_utils.generate_dummy_fire(
            datetime.datetime(2018,11,9), 4,
            {"center_latitude": 40, "center_longitude": -110}
        )
        expected["id"] = f["id"] # id is randomly generated
        assert expected == f


class TestFillInDummyFires(object):

    def setup(self):
        self.fires = [
            {"id": 1},
            {"id": 2},
            {"id": 1}
        ]
        self.original_fires = copy.deepcopy(self.fires)

        self.fire_sets = [
            [self.fires[0], self.fires[2]],  # id 1
            [self.fires[1]]  # id 2
        ]
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

    def test_one_proc_no_dummy_fires_needed(self, reset_config):
        hysplit_utils.fill_in_dummy_fires(self.fire_sets, self.fires, 1,
            datetime.datetime(2018,11,9), 4,
            {"center_latitude": 40, "center_longitude": -110})
        assert self.original_fires == self.fires
        assert self.original_fire_sets == self.fire_sets
        self.original_fires = copy.deepcopy(self.fires)
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

        self.original_fires = copy.deepcopy(self.fires)
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

        self.original_fires = copy.deepcopy(self.fires)
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

    def test_two_procs_no_dummy_fires_needed(self, reset_config):
        hysplit_utils.fill_in_dummy_fires(self.fire_sets, self.fires, 2,
            datetime.datetime(2018,11,9), 4,
            {"center_latitude": 40, "center_longitude": -110})
        assert self.original_fires == self.fires
        assert self.original_fire_sets == self.fire_sets
        self.original_fires = copy.deepcopy(self.fires)
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

        self.original_fires = copy.deepcopy(self.fires)
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

        self.original_fires = copy.deepcopy(self.fires)
        self.original_fire_sets = copy.deepcopy(self.fire_sets)

    def test_three_procs_one_dummy_fire_needed(self, reset_config):
        hysplit_utils.fill_in_dummy_fires(self.fire_sets, self.fires, 3,
            datetime.datetime(2018,11,9), 4,
            {"center_latitude": 40, "center_longitude": -110})
        assert len(self.fires) == 4
        assert self.fires[0:3] == self.original_fires
        assert len(self.fire_sets) == 3
        assert self.fire_sets[0:2] == self.original_fire_sets
        assert len(self.fire_sets[2]) == 1
        assert self.fire_sets[2][0] == self.fires[3]

    def test_four_procs_two_dummy_fires_needed(self, reset_config):
        hysplit_utils.fill_in_dummy_fires(self.fire_sets, self.fires, 4,
            datetime.datetime(2018,11,9), 4,
            {"center_latitude": 40, "center_longitude": -110})
        assert len(self.fires) == 5
        assert self.fires[0:3] == self.original_fires
        assert len(self.fire_sets) == 4
        assert self.fire_sets[0:2] == self.original_fire_sets
        assert len(self.fire_sets[2]) == 1
        assert self.fire_sets[2][0] == self.fires[3]
        assert len(self.fire_sets[3]) == 1
        assert self.fire_sets[3][0] == self.fires[4]

##
## Dispersion Grid
##

class TestKmPerLng(object):

    def test(self, reset_config):
        assert 111.32 == hysplit_utils.km_per_deg_lng(0)
        assert 78.71512688168647 == hysplit_utils.km_per_deg_lng(45)
        # Note: hysplit_utils.km_per_deg_lng(90) should equal 0
        #  using assert_approx_equal(0.0, hysplit_utils.km_per_deg_lng(90))
        #  fails, even thgouh the returned value is something like
        #  6.8163840840541674e-15.  So, just going to manually check
        #  that difference is insignificant
        assert hysplit_utils.km_per_deg_lng(90) < 0.000000000001

class TestSquareGridFromLatLng(object):

    def test(self, reset_config):
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

    def test_llc_projection(self, reset_config):
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
        spacing = 0.06705008458605
        expected = {
            "spacing_latitude": spacing,
            "spacing_longitude": spacing,
            "center_latitude": 36.5,
            "center_longitude": -119.0,
            "height_latitude": 17.5,
            "width_longitude": 25.0
        }
        assert expected == hysplit_utils.grid_params_from_grid(grid)

    def test_latlong_projection(self, reset_config):
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

    def test_user_defined_grid(self, reset_config):
        Config().set(True, "dispersion", "hysplit" , "USER_DEFINED_GRID")
        Config().set(36.5, "dispersion", "hysplit" , "CENTER_LATITUDE")
        Config().set(-119.0, "dispersion", "hysplit", "CENTER_LONGITUDE")
        Config().set(25.0, "dispersion", "hysplit" , "WIDTH_LONGITUDE")
        Config().set(17.5, "dispersion", "hysplit" , "HEIGHT_LATITUDE")
        Config().set(0.05, "dispersion", "hysplit" , "SPACING_LONGITUDE")
        Config().set(0.05, "dispersion", "hysplit" , "SPACING_LATITUDE")
        expected = {
            'center_latitude': 36.5,
            'center_longitude': -119.0,
            'height_latitude': 17.5,
            'spacing_latitude': 0.05,
            'spacing_longitude': 0.05,
            'width_longitude': 25.0
        }
        assert expected == hysplit_utils.get_grid_params()

    def test_grid(self, reset_config):
        Config().set( {
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
        }, "dispersion", "hysplit" , "grid")
        expected = {
            'center_latitude': 36.5,
            'center_longitude': -119.0,
            'height_latitude': 17.5,
            'spacing_latitude': 0.06705008458605,
            'spacing_longitude': 0.06705008458605,
            'width_longitude': 25.0
        }
        assert expected == hysplit_utils.get_grid_params()

    def test_compute_grid(self, reset_config):
        fires_one = [{'latitude': 40.0, 'longitude': -118.5}]
        fires_two = [
            {'latitude': 40.0, 'longitude': -118.5},
            {'latitude': 45.0, 'longitude': -117.5}
        ]

        ## Missing spacing

        Config().set(True, "dispersion", "hysplit" , "compute_grid")
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(fires=fires_one)
        assert e_info.value.args[0] == ("Config settings 'spacing_latitude' "
                "and 'spacing_longitude' required to compute hysplit grid")

        Config().reset()
        Config().set(True, "dispersion", "hysplit" , "compute_grid")
        Config().set(0.05, 'dispersion', 'hysplit', 'spacing_longitude')
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(fires=fires_one)
        assert e_info.value.args[0] == ("Config settings 'spacing_latitude' "
                "and 'spacing_longitude' required to compute hysplit grid")

        Config().reset()
        Config().set(True, "dispersion", "hysplit" , "compute_grid")
        Config().set(0.05, 'dispersion', 'hysplit', 'spacing_latitude')
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params(fires=fires_one)
        assert e_info.value.args[0] == ("Config settings 'spacing_latitude' "
                "and 'spacing_longitude' required to compute hysplit grid")


        ## no fires or two many fires

        Config().reset()
        Config().set(True, "dispersion", "hysplit" , "compute_grid")
        Config().set(0.05, 'dispersion', 'hysplit', 'spacing_latitude')
        Config().set(0.05, 'dispersion', 'hysplit', 'spacing_longitude')

        with raises(ValueError) as e_info:
            hysplit_utils.get_grid_params()
        assert e_info.value.args[0] == 'Option to compute grid only supported for runs with one fire'

        with raises(ValueError) as e_info:
            hysplit_utils.get_grid_params(fires=fires_two)
        assert e_info.value.args[0] == 'Option to compute grid only supported for runs with one fire'

        expected = {
            'center_latitude': 40.0,
            'center_longitude': -118.5,
            'height_latitude': 18.01801801801802,
            'spacing_latitude': 0.05,
            'spacing_longitude': 0.05,
            'width_longitude': 23.453239118438354
        }
        assert expected == hysplit_utils.get_grid_params(fires=fires_one)

        # custom grid length (default is 2000)
        Config().set(1000, 'dispersion', 'hysplit', 'grid_length')
        expected = {
            'center_latitude': 40.0,
            'center_longitude': -118.5,
            'height_latitude': 9.00900900900901,
            'spacing_latitude': 0.05,
            'spacing_longitude': 0.05,
            'width_longitude': 11.726619559219177
        }
        assert expected == hysplit_utils.get_grid_params(fires=fires_one)

    def test_met_info(self, reset_config):
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
            'spacing_latitude': 0.06705008458605,
            'spacing_longitude': 0.06705008458605,
            'width_longitude': 25.0
        }
        assert expected == hysplit_utils.get_grid_params(met_info=met_info)

    def test_allow_undefined(self, reset_config):
        expected = {}
        assert expected == hysplit_utils.get_grid_params(allow_undefined=True)

    def test_fail(self, reset_config):
        with raises(BlueSkyConfigurationError) as e_info:
            hysplit_utils.get_grid_params()
        assert e_info.value.args[0] == 'Specify hysplit dispersion grid'
