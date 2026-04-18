"""bluesky.dispersers.hysplit.pardump_io

Read/write helpers for HYSPLIT PARDUMP/PARINIT particle state files.

The file format (see hysplit.v5.2.3/library/hysplit/parout.f and parinp.f) is
big-endian Fortran unformatted sequential binary:

  Header record (one per timestep):
      7 int32: numpar, numpol, year, month, day, hour, minute

  Per-particle records (numpar of them):
      mass_data  -- numpol float32 (pollutant masses; BlueSky/HYSPLIT use grams)
      pos_data   -- float32 positions (lat, lon, height, ...)
      meta_data  -- int32 metadata (age, source index, ...)

Each Fortran record is wrapped with 4-byte length markers at both ends.

PARINIT files contain a single header + particle block. PARDUMP files
concatenate one or more such blocks; this module only handles the
single-block form used by PARINIT.
"""

__author__ = "Stuart Illson"

import struct

__all__ = [
    'read_parinit',
    'write_parinit',
    'particle_total_mass',
]

# Big-endian 7-int header: numpar, numpol, yr, mo, da, hr, mn
HEADER_FMT = ">iiiiiii"
HEADER_SIZE = struct.calcsize(HEADER_FMT)


def read_parinit(path):
    """Read a PARINIT file.

    Returns (header, particles), where header is a 7-tuple (numpar, numpol,
    yr, mo, da, hr, mn) and particles is a list of (mass_bytes, pos_bytes,
    meta_bytes).

    Raises ValueError on a truncated or malformed file.
    """
    with open(path, "rb") as f:
        header_data = _read_record(f)
        if header_data is None or len(header_data) != HEADER_SIZE:
            raise ValueError("Invalid PARINIT header in %s" % path)
        header = struct.unpack(HEADER_FMT, header_data)
        numpar = header[0]

        particles = []
        for i in range(numpar):
            mass = _read_record(f)
            pos = _read_record(f)
            meta = _read_record(f)
            if mass is None or pos is None or meta is None:
                raise ValueError("Truncated particle record %d of %d in %s"
                    % (i, numpar, path))
            particles.append((mass, pos, meta))

    return header, particles


def write_parinit(path, header, particles):
    """Write a PARINIT file.

    header[0] (numpar) is replaced with len(particles) so callers don't need
    to keep it in sync after filtering.
    """
    new_header = (len(particles),) + tuple(header[1:])
    with open(path, "wb") as f:
        _write_record(f, struct.pack(HEADER_FMT, *new_header))
        for mass, pos, meta in particles:
            _write_record(f, mass)
            _write_record(f, pos)
            _write_record(f, meta)


def particle_total_mass(mass_bytes, numpol):
    """Sum of pollutant masses for a single particle (grams)."""
    return sum(struct.unpack(">%df" % numpol, mass_bytes))


def _read_record(f):
    # Fortran unformatted sequential: [4-byte len][data][4-byte len]
    size_bytes = f.read(4)
    if len(size_bytes) < 4:
        return None
    size = struct.unpack(">i", size_bytes)[0]
    data = f.read(size)
    if len(data) < size:
        return None
    f.read(4)  # trailing length marker
    return data


def _write_record(f, data):
    n = len(data)
    f.write(struct.pack(">i", n))
    f.write(data)
    f.write(struct.pack(">i", n))
