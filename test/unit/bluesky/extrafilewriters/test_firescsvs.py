"""Unit tests for bluesky.visualizers.dispersion.hysplit"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.extrafilewriters import firescsvs

class TestFiresCsvsPickRepresentativeFuelbed(object):

    def test_invalid_fuelbed(self):
        g = {
            "fuelbeds": 'sdf'
        }
        with raises(TypeError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''

        g = {
            "fuelbeds": [
                {"sdf_fccs_id": "46","pct": 100.0}
            ]
        }
        with raises(KeyError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''
        g = {
            "fuelbeds": [
                {"fccs_id": "46","sdfsdfpct": 100.0}
            ]
        }
        with raises(KeyError) as e_info:
            firescsvs._pick_representative_fuelbed({}, g)
        # TODO: assert e_info.value.args[0] == '...''

    def test_no_fuelbeds(self):
        g = {}
        assert None == firescsvs._pick_representative_fuelbed({}, g)
        g = {
            "growth": []
        }
        assert None == firescsvs._pick_representative_fuelbed({}, g)

    def test_one_fuelbed(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0}
            ]
        }
        assert "46" == firescsvs._pick_representative_fuelbed({}, g)

    def test_three_fuelbed(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 10.0},
                {"fccs_id": "47","pct": 60.0},
                {"fccs_id": "48","pct": 30.0}
            ]
        }
        assert "47" == firescsvs._pick_representative_fuelbed({}, g)

    def test_two_equal_size_fuelbeds(self):
        g = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0},
                {"fccs_id": "44","pct": 100.0}
            ]
        }
        assert "46" == firescsvs._pick_representative_fuelbed({}, g)
