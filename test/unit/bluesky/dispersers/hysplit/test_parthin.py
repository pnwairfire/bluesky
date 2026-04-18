"""Unit tests for bluesky.dispersers.hysplit.parthin
"""

import struct

from pytest import raises

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.dispersers.hysplit import pardump_io
from bluesky.dispersers.hysplit.parthin import Parthinner, summarize_parinit


def _config_getter(parthin_dict):
    """Build a config getter that returns values from a single 'parthin' dict."""
    def g(*keys, **kwargs):
        assert keys[0] == 'parthin'
        return parthin_dict.get(keys[1])
    return g


def _write_parinit(path, masses, numpol=1):
    """Helper: write a PARINIT file from a flat list of per-particle masses."""
    particles = []
    for m in masses:
        mass = struct.pack(">%df" % numpol, *([m] * numpol))
        pos = struct.pack(">5f", 0, 0, 0, 0, 0)
        meta = struct.pack(">3i", 0, 0, 0)
        particles.append((mass, pos, meta))
    header = (len(particles), numpol, 2025, 9, 1, 0, 0)
    pardump_io.write_parinit(str(path), header, particles)


class TestParthinnerConfig():

    def test_disabled_by_default(self):
        p = Parthinner(_config_getter({"enabled": False}))
        assert p.enabled is False

    def test_enabled_with_min_mass(self):
        p = Parthinner(_config_getter({
            "enabled": True, "min_mass_grams": 1.0,
        }))
        assert p.enabled is True

    def test_mutually_exclusive_modes_raise(self):
        with raises(BlueSkyConfigurationError):
            Parthinner(_config_getter({
                "enabled": True,
                "min_mass_grams": 1.0,
                "thin_bins": [[2.0, 0.5]],
            }))

    def test_bins_must_be_ascending(self):
        with raises(BlueSkyConfigurationError):
            Parthinner(_config_getter({
                "enabled": True,
                "thin_bins": [[2.0, 0.5], [1.0, 0.25]],
            }))

    def test_thin_rate_out_of_range_raises(self):
        with raises(BlueSkyConfigurationError):
            Parthinner(_config_getter({
                "enabled": True,
                "thin_bins": [[1.0, 1.5]],
            }))

    def test_empty_bins_raises(self):
        with raises(BlueSkyConfigurationError):
            Parthinner(_config_getter({
                "enabled": True,
                "thin_bins": [],
            }))


class TestParthinnerFiltering():

    def test_min_mass_drops_below_threshold(self, tmp_path):
        src = tmp_path / "src"
        dest = tmp_path / "dest"
        _write_parinit(src, [0.1, 0.5, 1.0, 2.0, 5.0])

        p = Parthinner(_config_getter({
            "enabled": True, "min_mass_grams": 1.0,
        }))
        kept, total = p.thin(str(src), str(dest))

        # >= 1.0 kept: 1.0, 2.0, 5.0
        assert total == 5
        assert kept == 3

    def test_thin_rate_zero_is_no_op(self, tmp_path):
        src = tmp_path / "src"
        dest = tmp_path / "dest"
        _write_parinit(src, [0.1, 0.5, 1.0, 5.0])

        p = Parthinner(_config_getter({
            "enabled": True, "thin_bins": [[10.0, 0.0]],
        }))
        kept, total = p.thin(str(src), str(dest))

        assert kept == total == 4

    def test_thin_rate_one_drops_everything_in_range(self, tmp_path):
        src = tmp_path / "src"
        dest = tmp_path / "dest"
        _write_parinit(src, [0.1, 0.5, 1.0, 5.0])

        p = Parthinner(_config_getter({
            "enabled": True, "thin_bins": [[2.0, 1.0]],
        }))
        kept, total = p.thin(str(src), str(dest))

        # 5.0 exceeds highest upper bound -> kept; rest dropped
        assert total == 4
        assert kept == 1


class TestSummarizeParinit():

    def test_empty_file(self, tmp_path):
        path = tmp_path / "PARINIT"
        _write_parinit(path, [])

        s = summarize_parinit(str(path))
        assert s["total_particles"] == 0
        assert s["total_mass_grams"] == 0.0
        assert s["mass_stats"] is None

    def test_basic_shape(self, tmp_path):
        path = tmp_path / "PARINIT"
        _write_parinit(path, [1.0] * 100)

        s = summarize_parinit(str(path))
        assert s["total_particles"] == 100
        assert s["total_mass_grams"] == 100.0
        assert s["mass_stats"]["min"] == 1.0
        assert s["mass_stats"]["max"] == 1.0
        # Top 99% of mass is 99 particles (uniform distribution)
        assert s["mass_concentration"][0.99]["particles"] == 99
        # Nothing below 0.1g
        assert s["particles_below"][0.1]["particles"] == 0
