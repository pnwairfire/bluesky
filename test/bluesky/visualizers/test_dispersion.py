"""Unit tests for bluesky.configuration"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from py.test import raises

from bluesky.visualizers import dispersion

class TestHysplitVisualizerPickRepresentativeFuelbed(object):

    def test_invalid_fuelbed(self):
        f = {
            "fuelbeds": 'sdf'
        }
        with raises(ValueError) as e_info:
            dispersion._pick_representative_fuelbed(f)
        # TODO: assert e_info.value.message == '...''

        f = {
            "fuelbeds": [
                {"sdf_fccs_id": "46","pct": 100.0}
            ]
        }
        with raises(ValueError) as e_info:
            dispersion._pick_representative_fuelbed(f)
        # TODO: assert e_info.value.message == '...''
        f = {
            "fuelbeds": [
                {"fccs_id": "46","sdfsdfpct": 100.0}
            ]
        }
        with raises(ValueError) as e_info:
            dispersion._pick_representative_fuelbed(f)
        # TODO: assert e_info.value.message == '...''

    def test_no_fuelbeds(self):
        f = {}
        assert None == dispersion._pick_representative_fuelbed(f)

    def test_one_fuelbed(self):
        f = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0}
            ]
        }
        assert "46" == dispersion._pick_representative_fuelbed(f)

    def test_three_fuelbed(self):
        f = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 10.0},
                {"fccs_id": "47","pct": 60.0},
                {"fccs_id": "48","pct": 30.0}
            ]
        }
        assert "47" == dispersion._pick_representative_fuelbed(f)

    def test_two_equal_size_fuelbeds(self):
        f = {
            "fuelbeds": [
                {"fccs_id": "46","pct": 100.0},
                {"fccs_id": "44","pct": 100.0}
            ]
        }
        assert "46" == dispersion._pick_representative_fuelbed(f)
