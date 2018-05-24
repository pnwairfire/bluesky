"""Unit tests for bluesky.dispersers.hysplit.hysplit
"""

import datetime
import os

from bluesky.dispersers.hysplit import hysplit

class TestGetBinaries(object):
    # Notes:
    #    - hysplit._get_binaries will always be passed a dict;
    #    - the dict will have all lowercase top level keys

    def test_empty_config(self):
        config = {}
        expected = {
            'HYSPLIT': "hycs_std",
            'HYSPLIT_MPI': "hycm_std",
            'NCEA': "ncea",
            'NCKS': "ncks",
            'MPI': "mpiexec",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config) == expected

    def test_old(self):
        config = {
            'hysplit_binary': 'zzz'
        }
        expected = {
            'HYSPLIT': "zzz",
            'HYSPLIT_MPI': "hycm_std",
            'NCEA': "ncea",
            'NCKS': "ncks",
            'MPI': "mpiexec",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config) == expected

    def test_old_and_new(self):
        config = {
            'mpiexec': 'foo',
            'binaries': {
                'MPI': 'bar', # takes precedence over 'MPIEXEC'
                'ncea': 'sdfsdf',
                'NCKS': 'werwer'
            },
            'hysplit_binary': 'zzz',
            'hysplit_mpi_binary': 'ttt'
        }
        expected = {
            'HYSPLIT': "zzz",
            'HYSPLIT_MPI': "ttt",
            'NCEA': "sdfsdf",
            'NCKS': "werwer",
            'MPI': "bar",
            'HYSPLIT2NETCDF': "hysplit2netcdf"
        }
        assert hysplit._get_binaries(config) == expected

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

