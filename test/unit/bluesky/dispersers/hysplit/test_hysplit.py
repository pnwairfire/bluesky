"""Unit tests for bluesky.dispersers.hysplit.hysplit
"""


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
