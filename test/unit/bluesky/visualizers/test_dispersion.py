"""Unit tests for bluesky.configuration"""

__author__ = "Joel Dubowy"

from py.test import raises

from bluesky.visualizers.dispersion import hysplit

class TestHysplitVisualizerPickRepresentativeFuelbed(object):

    def test_invalid_fuelbed(self):
        f = {
            "fuelbeds": 'sdf'
        }
        with raises(TypeError) as e_info:
            hysplit._pick_representative_fuelbed(f, {})
        # TODO: assert e_info.value.args[0] == '...''

        f = {
            "fuelbeds": [
                {"sdf_fccs_id": "46","pct": 100.0}
            ]
        }
        with raises(KeyError) as e_info:
            hysplit._pick_representative_fuelbed(f, {})
        # TODO: assert e_info.value.args[0] == '...''
        f = {
            "fuelbeds": [
                {"fccs_id": "46","sdfsdfpct": 100.0}
            ]
        }
        with raises(KeyError) as e_info:
            hysplit._pick_representative_fuelbed(f, {})
        # TODO: assert e_info.value.args[0] == '...''

    def test_no_fuelbeds(self):
        f = {}
        assert None == hysplit._pick_representative_fuelbed(f, {})

    def test_one_fuelbed(self):
        f = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0}
            ]
        }
        assert "46" == hysplit._pick_representative_fuelbed(f, {})

    def test_three_fuelbed(self):
        f = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 10.0},
                {"fccs_id": "47","pct": 60.0},
                {"fccs_id": "48","pct": 30.0}
            ]
        }
        assert "47" == hysplit._pick_representative_fuelbed(f, {})

    def test_two_equal_size_fuelbeds(self):
        f = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0},
                {"fccs_id": "44","pct": 100.0}
            ]
        }
        assert "46" == hysplit._pick_representative_fuelbed(f, {})
