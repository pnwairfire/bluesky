"""Unit tests for bluesky.dispersers.hysplit.hysplit
"""

import datetime
import os

import afconfig
from py.test import raises

from bluesky.config import to_lowercase_keys
from bluesky.dispersers.hysplit import hysplit

class TestGetBinaries(object):
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
            'HYSPLIT': "hycs_std",
            'HYSPLIT_MPI': "hycm_std",
            'NCEA': "ncea",
            'NCKS': "ncks",
            'MPI': "mpiexec",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config_getter) == expected

    def test_old(self):
        config_getter = self._config_getter({
            'hysplit_binary': 'zzz'
        })
        expected = {
            'HYSPLIT': "zzz",
            'HYSPLIT_MPI': "hycm_std",
            'NCEA': "ncea",
            'NCKS': "ncks",
            'MPI': "mpiexec",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config_getter) == expected

    def test_old_and_new(self):
        config_getter = self._config_getter({
            'mpiexec': 'foo',
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

class TestSetMetInfo(object):

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

class TestAdjustDispersionWindowForAvailableMet(object):

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
