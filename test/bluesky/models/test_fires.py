from py.test import raises

try:
    from bluesky.models import fires
except:
    import os
    import sys
    root_dir = os.path.abspath(os.path.join(sys.path[0], '../../../'))
    sys.path.insert(0, root_dir)
    from bluesky.models import fires

class TestFires:

    def test_from_json(self):
        with raises(ValueError):
            fires.Fire.from_json('')
        with raises(ValueError):
            fires.Fire.from_json('""')
        with raises(ValueError):
            fires.Fire.from_json('"sdf"')
        with raises(ValueError):
            fires.Fire.from_json('null')

        assert [] == fires.Fire.from_json('[]')

        # TODO: test case of single fire object
        # TODO: test case of non-empty array of fire objects
