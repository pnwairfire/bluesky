"""Unit tests for bluesky.dispersers.hysplit.pardump_io
"""

import os
import struct

from pytest import raises, approx

from bluesky.dispersers.hysplit import pardump_io


def _fortran_record(data):
    n = len(data)
    return struct.pack(">i", n) + data + struct.pack(">i", n)


def _make_parinit_bytes(masses_per_particle, numpol):
    """Build PARINIT file bytes manually (avoids depending on write_parinit)."""
    header = struct.pack(">iiiiiii",
        len(masses_per_particle), numpol, 2025, 9, 1, 0, 0)
    out = _fortran_record(header)
    for masses in masses_per_particle:
        out += _fortran_record(struct.pack(">%df" % numpol, *masses))
        out += _fortran_record(struct.pack(">5f", 0, 0, 0, 0, 0))
        out += _fortran_record(struct.pack(">3i", 0, 0, 0))
    return out


class TestReadParinit():

    def test_single_particle(self, tmp_path):
        path = tmp_path / "PARINIT"
        path.write_bytes(_make_parinit_bytes([[1.5]], numpol=1))

        header, particles = pardump_io.read_parinit(str(path))
        assert header == (1, 1, 2025, 9, 1, 0, 0)
        assert len(particles) == 1

    def test_multiple_particles_multi_pollutant(self, tmp_path):
        path = tmp_path / "PARINIT"
        masses = [[1.0, 0.5], [2.0, 1.0], [3.0, 1.5]]
        path.write_bytes(_make_parinit_bytes(masses, numpol=2))

        header, particles = pardump_io.read_parinit(str(path))
        assert header[0] == 3
        assert header[1] == 2
        assert len(particles) == 3

    def test_truncated_file_raises(self, tmp_path):
        path = tmp_path / "PARINIT"
        full = _make_parinit_bytes([[1.0], [2.0]], numpol=1)
        # Chop off the last particle's metadata record
        path.write_bytes(full[:-16])

        with raises(ValueError):
            pardump_io.read_parinit(str(path))


class TestWriteParinit():

    def test_roundtrip_preserves_particles(self, tmp_path):
        src = tmp_path / "src"
        dest = tmp_path / "dest"
        src.write_bytes(_make_parinit_bytes([[1.0], [2.0], [3.0]], numpol=1))

        header, particles = pardump_io.read_parinit(str(src))
        pardump_io.write_parinit(str(dest), header, particles)

        assert src.read_bytes() == dest.read_bytes()

    def test_header_numpar_updated_on_filter(self, tmp_path):
        src = tmp_path / "src"
        dest = tmp_path / "dest"
        src.write_bytes(_make_parinit_bytes([[1.0], [2.0], [3.0]], numpol=1))

        header, particles = pardump_io.read_parinit(str(src))
        # Write just the first two
        pardump_io.write_parinit(str(dest), header, particles[:2])

        new_header, new_particles = pardump_io.read_parinit(str(dest))
        assert new_header[0] == 2
        assert len(new_particles) == 2
        # Other header fields preserved
        assert new_header[1:] == header[1:]


class TestParticleTotalMass():

    def test_single_pollutant(self):
        mass_bytes = struct.pack(">1f", 3.25)
        assert pardump_io.particle_total_mass(mass_bytes, 1) == approx(3.25)

    def test_multi_pollutant_sums(self):
        mass_bytes = struct.pack(">3f", 1.0, 0.5, 0.25)
        assert pardump_io.particle_total_mass(mass_bytes, 3) == approx(1.75)
