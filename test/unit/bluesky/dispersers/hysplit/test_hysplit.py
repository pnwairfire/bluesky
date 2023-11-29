"""Unit tests for bluesky.dispersers.hysplit.hysplit
"""

import datetime
import os

import afconfig
from pytest import raises, approx

from bluesky.config import to_lowercase_keys
from bluesky.dispersers.hysplit import hysplit
from bluesky.dispersers import SQUARE_METERS_PER_ACRE, GRAMS_PER_TON
from bluesky.dispersers.hysplit.emissions_file_utils import (
    _compute_emissions_rows_data,
    _reduce_and_reallocate_vertical_levels
)

class TestGetBinaries():
    # Notes:
    #    - hysplit._get_binaries will always be passed a dict;
    #    - the dict will have all lowercase top level keys

    def _config_getter(self, config):
        config = to_lowercase_keys(config)
        def getter(*keys, **kwargs):
            keys = [k.lower() for k in keys]
            return afconfig.get_config_value(config, *keys,
                fail_on_missing_key=not kwargs.get('allow_missing'))
        return getter

    def test_empty_config(self):
        config_getter = self._config_getter({})
        expected = {
            'HYSPLIT': "hycs_std-v5.2.3",
            'HYSPLIT_MPI': "hycm_std-v5.2.3-openmpi",
            'NCEA': "ncea",
            'NCKS': "ncks",
            'MPI': "mpiexec.openmpi",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config_getter) == expected

    def test_old(self):
        config_getter = self._config_getter({
            'hysplit_binary': 'zzz'
        })
        expected = {
            'HYSPLIT': "zzz",
            'HYSPLIT_MPI': "hycm_std-v5.2.3-openmpi",
            'NCEA': "ncea",
            'NCKS': "ncks",
            'MPI': "mpiexec.openmpi",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config_getter) == expected

    def test_old_and_new(self):
        config_getter = self._config_getter({
            'mpiexec.openmpi': 'foo',
            'binaries': {
                'MPI': 'bar', # takes precedence over 'MPIEXEC'
                'ncea': 'sdfsdf',
                'NCKS': 'werwer'
            },
            'hysplit_binary': 'zzz',
            'hysplit_mpi_binary': 'ttt'
        })
        expected = {
            'HYSPLIT': "zzz",
            'HYSPLIT_MPI': "ttt",
            'NCEA': "sdfsdf",
            'NCKS': "werwer",
            'MPI': "bar",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config_getter) == expected

class TestSetMetInfo():

    def test_with_grid(self, monkeypatch):
        monkeypatch.setattr(os.path, 'exists', lambda e: True)
        met_info = {
            'grid': {'foo':'bar'},
            'files': [
                {
                    'first_hour': '2014-05-29T00:00:00',
                    'file': 'f',
                    'last_hour': '2014-05-29T03:00:00'
                },
                # missing 2014-05-29T12:00:00 through 2014-05-29T23:00:00
                {
                    'first_hour': '2014-05-30T11:00:00',
                    'file': 'f2',
                    'last_hour': '2014-05-30T12:00:00'
                }
            ]
        }

        expected = {
            'grid': {'foo':'bar'},
            'files': set(['f', 'f2']),
            'hours': set([
                datetime.datetime(2014, 5, 29, 0, 0, 0),
                datetime.datetime(2014, 5, 29, 1, 0, 0),
                datetime.datetime(2014, 5, 29, 2, 0, 0),
                datetime.datetime(2014, 5, 29, 3, 0, 0),
                datetime.datetime(2014, 5, 30, 11, 0, 0),
                datetime.datetime(2014, 5, 30, 12, 0, 0),
            ])
        }

        hysplitDisperser = hysplit.HYSPLITDispersion(met_info)
        assert hysplitDisperser._met_info == expected

    def test_without_grid(self, monkeypatch):
        monkeypatch.setattr(os.path, 'exists', lambda e: True)
        met_info = {
            'files': [
                {
                    'first_hour': '2014-05-29T00:00:00',
                    'file': 'f',
                    'last_hour': '2014-05-29T03:00:00'
                }
            ]
        }

        expected = {
            'files': set(['f']),
            'hours': set([
                datetime.datetime(2014, 5, 29, 0, 0, 0),
                datetime.datetime(2014, 5, 29, 1, 0, 0),
                datetime.datetime(2014, 5, 29, 2, 0, 0),
                datetime.datetime(2014, 5, 29, 3, 0, 0)
            ])
        }

        hysplitDisperser = hysplit.HYSPLITDispersion(met_info)
        assert hysplitDisperser._met_info == expected

class TestAdjustDispersionWindowForAvailableMet():

    # class HYSPLITDispersionWithoutSetMetInfo(hysplit.HYSPLITDispersion):

    #     def _set_met_info(self, met_info):
    #         pass

    def set_up_monkey_patched_disperser(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        self.hysplitDisperser = hysplit.HYSPLITDispersion({})
        self.hysplitDisperser._met_info = {
            'files': [ 'f', 'f2'],
            'hours': set([
                datetime.datetime(2014, 5, 29, 1, 0, 0),
                datetime.datetime(2014, 5, 29, 2, 0, 0),
                datetime.datetime(2014, 5, 29, 3, 0, 0),
                datetime.datetime(2014, 5, 30, 10, 0, 0),
                datetime.datetime(2014, 5, 30, 11, 0, 0),
                datetime.datetime(2014, 5, 30, 12, 0, 0),
            ])
        }
        self.hysplitDisperser._warnings = []


    def test_complete_met_for_dispersion_window(self, monkeypatch):
        self.set_up_monkey_patched_disperser(monkeypatch)

        self.hysplitDisperser._model_start = datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        self.hysplitDisperser._num_hours = 2
        self.hysplitDisperser._adjust_dispersion_window_for_available_met()
        assert self.hysplitDisperser._model_start == datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        assert self.hysplitDisperser._num_hours == 2
        assert self.hysplitDisperser._warnings == []

    def test_no_met_for_dispersion_window(self, monkeypatch):
        self.set_up_monkey_patched_disperser(monkeypatch)

        self.hysplitDisperser._model_start = datetime.datetime(
            2014, 5, 29, 5, 0, 0)
        self.hysplitDisperser._num_hours = 2
        with raises(ValueError) as e_info:
            self.hysplitDisperser._adjust_dispersion_window_for_available_met()
        assert e_info.value.args[0] == "No ARL met data for first hour of dispersion window"

    def test_met_missing_at_begining_of_dispersion_window(self, monkeypatch):
        self.set_up_monkey_patched_disperser(monkeypatch)

        self.hysplitDisperser._model_start = datetime.datetime(
            2014, 5, 29, 0, 0, 0)
        self.hysplitDisperser._num_hours = 2
        with raises(ValueError) as e_info:
            self.hysplitDisperser._adjust_dispersion_window_for_available_met()
        assert e_info.value.args[0] == "No ARL met data for first hour of dispersion window"

    def test_met_missing_in_middle_of_dispersion_window(self, monkeypatch):
        self.set_up_monkey_patched_disperser(monkeypatch)

        self.hysplitDisperser._model_start = datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        self.hysplitDisperser._num_hours = 35
        self.hysplitDisperser._adjust_dispersion_window_for_available_met()
        assert self.hysplitDisperser._model_start == datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        assert self.hysplitDisperser._num_hours == 3
        assert self.hysplitDisperser._warnings == [
            {"message": "Incomplete met. Running dispersion for"
                " 3 hours instead of 35"}
        ]

    def test_met_missing_at_end_of_dispersion_window(self, monkeypatch):
        self.set_up_monkey_patched_disperser(monkeypatch)

        self.hysplitDisperser._model_start = datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        self.hysplitDisperser._num_hours = 5
        self.hysplitDisperser._adjust_dispersion_window_for_available_met()
        assert self.hysplitDisperser._model_start == datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        assert self.hysplitDisperser._num_hours == 3
        assert self.hysplitDisperser._warnings == [
            {"message": "Incomplete met. Running dispersion for"
                " 3 hours instead of 5"}
        ]


    def test_met_missing_in_middle_and_at_end_of_dispersion_window(self, monkeypatch):
        self.set_up_monkey_patched_disperser(monkeypatch)

        self.hysplitDisperser._model_start = datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        self.hysplitDisperser._num_hours = 48
        self.hysplitDisperser._adjust_dispersion_window_for_available_met()
        assert self.hysplitDisperser._model_start == datetime.datetime(
            2014, 5, 29, 1, 0, 0)
        assert self.hysplitDisperser._num_hours == 3
        assert self.hysplitDisperser._warnings == [
            {"message": "Incomplete met. Running dispersion for"
                " 3 hours instead of 48"}
        ]

class TestReduceVerticalLevels():

    def test_equal_fractions_reduction_factor_4(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 4

        plumerise_hour = {
            'heights': [
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            'emission_fractions': [
                0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
                0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05
            ],
            'smolder_fraction': 0.0
        }

        expected_fractions = [0.25, 0.25, 0.25, 0.25, 0]
        expected_heights = [1400, 1800, 2200, 2600, 3000]

        heights, fractions = _reduce_and_reallocate_vertical_levels(
            plumerise_hour, h._reduction_factor)

        assert heights == expected_heights
        assert fractions == expected_fractions

    def test_varying_fractions_reduction_factor_5(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 5

        plumerise_hour = {
            "heights":[
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            "emission_fractions": [
                0.05, 0.05, 0.1, 0.1, 0.1, 0.04, 0.04, 0.04, 0.04, 0.04,
                0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04
            ]
        }

        expected_fractions = [0.5, 0.25, 0.25, 0]
        expected_heights = [1500, 2000, 2500, 3000]

        heights, fractions = _reduce_and_reallocate_vertical_levels(
            plumerise_hour, h._reduction_factor)

        assert heights == expected_heights
        assert fractions == expected_fractions

    def test_all_emissions_in_top_reduced_level_reduction_factor_4(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 4

        plumerise_hour = {
            "heights":[
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            "emission_fractions": [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.25, 0.25, 0.25
            ]
        }

        expected_fractions = [0.25, 0.25, 0.25, 0.25, 0]
        expected_heights = [1400, 1800, 2200, 2600, 3000]

        heights, fractions = _reduce_and_reallocate_vertical_levels(
            plumerise_hour, h._reduction_factor)

        assert heights == expected_heights
        assert fractions == expected_fractions

    def test_varying_fractions_reduction_factor_20(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 20

        plumerise_hour = {
            "heights":[
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            "emission_fractions": [
                0.05, 0.05, 0.1, 0.1, 0.1, 0.04, 0.04, 0.04, 0.04, 0.04,
                0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04
            ]
        }

        expected_fractions = [1.0]
        expected_heights = [3000]

        heights, fractions = _reduce_and_reallocate_vertical_levels(
            plumerise_hour, h._reduction_factor)

        assert heights == expected_heights
        assert fractions == approx(expected_fractions, abs=0.00001)


class TestGetEmissionsRowsDataForLatLon():

    def test_equal_fractions_reduction_factor_4_not_dummy(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 4

        plumerise_hour = {
            'heights': [
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            'emission_fractions': [
                0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05,
                0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05
            ],
            'smolder_fraction': 0.0
        }
        pm25 = 10
        area = 10
        dummy = False

        expected_area = area * SQUARE_METERS_PER_ACRE
        expected_rows = [
            (10.0, 0.0, expected_area, 0.0),
            (1400, 0.25 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (1800, 0.25 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (2200, 0.25 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (2600, 0.25 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (3000, 0.0, expected_area, 0.0)
        ]

        rows = _compute_emissions_rows_data(h.config, h._reduction_factor,
            plumerise_hour, pm25, area, dummy)

        assert rows == expected_rows

    def test_varying_fractions_reduction_factor_5(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 5

        plumerise_hour = {
            "heights":[
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            "emission_fractions": [
                0.05, 0.05, 0.1, 0.1, 0.1, 0.04, 0.04, 0.04, 0.04, 0.04,
                0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04
            ],
            'smolder_fraction': 0.0
        }
        pm25 = 10
        area = 10
        dummy = False

        expected_area = area * SQUARE_METERS_PER_ACRE
        expected_rows = [
            (10.0, 0.0, expected_area, 0.0),
            (1500, 0.5 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (2000, 0.25 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (2500, 0.25 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (3000, 0.0, expected_area, 0.0)
        ]

        rows = _compute_emissions_rows_data(h.config, h._reduction_factor,
            plumerise_hour, pm25, area, dummy)

        assert rows == expected_rows


    def test_all_emissions_in_top_reduced_level_reduction_factor_4(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 4

        plumerise_hour = {
            "heights":[
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            "emission_fractions": [
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.25, 0.25, 0.25
            ],
            'smolder_fraction': 0.2  # Note that this is non-zero for this test
        }
        pm25 = 10
        area = 10
        dummy = False

        expected_area = area * SQUARE_METERS_PER_ACRE
        expected_rows = [
            (10.0, 0.2 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (1400, 0.2 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (1800, 0.2 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (2200, 0.2 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (2600, 0.2 * pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (3000, 0.0, expected_area, 0.0)
        ]

        rows = _compute_emissions_rows_data(h.config, h._reduction_factor,
            plumerise_hour, pm25, area, dummy)

        assert len(rows) == len(expected_rows)
        for i, r in enumerate(rows):
            assert r == approx(expected_rows[i], abs=0.00001)

    def test_varying_fractions_reduction_factor_20(self, monkeypatch):
        monkeypatch.setattr(hysplit.HYSPLITDispersion, '_set_met_info',
            lambda self, met_info: None)
        h = hysplit.HYSPLITDispersion({})
        h._reduction_factor = 20

        plumerise_hour = {
            "heights":[
                1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900,
                2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000
            ],
            "emission_fractions": [
                0.05, 0.05, 0.1, 0.1, 0.1, 0.04, 0.04, 0.04, 0.04, 0.04,
                0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04
            ],
            'smolder_fraction': 0.0
        }
        pm25 = 10
        area = 10
        dummy = False

        expected_area = area * SQUARE_METERS_PER_ACRE
        expected_rows = [
            (10.0, pm25 * GRAMS_PER_TON, expected_area, 0.0),
            (3000, 0.0, expected_area, 0.0)
        ]

        rows = _compute_emissions_rows_data(h.config, h._reduction_factor,
            plumerise_hour, pm25, area, dummy)

        assert rows == expected_rows
