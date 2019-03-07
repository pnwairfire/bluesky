"""Unit tests for bluesky.dispersers.DispersionBase
"""

from bluesky.dispersers import DispersionBase

class FakeDisperser(DispersionBase):

    def _required_growth_fields(self):
        pass

    def _run(wdir):
        pass

class TestDispersionBase(object):

    def test_config(self):
        config = {
            "QCYCLE": 2.2,
            "numpar": 333,
            "FOO": 34,
            "bar": 100

        }
        d = FakeDisperser({}, **config)
        # non-overridden default
        assert d.config('MGMIN') == 10
        assert d.config('mgmin') == 10
        # user overridden default specified by user as uppercase
        assert d.config('QCYCLE') == 2.2
        assert d.config('qcycle') == 2.2
        # user overridden default specified by user as lowercase
        assert d.config('NUMPAR') == 333
        assert d.config('numpar') == 333
        # user defined config setting without default, specified by user as uppercase
        assert d.config('FOO') == 34
        assert d.config('foo') == 34
        # user defined config setting without default, specified by user as lowercase
        assert d.config('BAR') == 100
        assert d.config('bar') == 100
