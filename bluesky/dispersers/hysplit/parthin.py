"""bluesky.dispersers.hysplit.parthin

Particle thinning for PARINIT files. Reduces the particle count that HYSPLIT
reads when continuing from a previous run's PARDUMP. Enables the user to set
particle mass limits to either drop particles with negligible mass, or sub-sample
particles in given mass ranges. Since HYSPLIT produces the same number of particles
per source, and due to depositon factors, simulations may be running with a large
number of particles carrying almost no mass.

Two modes, configured under 'dispersion.hysplit.parthin':

  min_mass_grams  -- drop particles whose total mass is below this threshold.
                     Equivalent to a thin_bins entry of [threshold, 1.0].
  thin_bins       -- list of [upper_mass, thin_rate] pairs defining ascending,
                     non-overlapping mass ranges. Each bin covers masses from
                     the previous bin's upper_mass (inclusive) up to its own
                     upper_mass (exclusive); the first bin starts at 0.
                     Particles within a bin are removed with probability
                     thin_rate. Particles exceeding the highest upper_mass are
                     always kept. A thin_rate of 1.0 is equivalent to removing
                     100%.

The two modes are mutually exclusive. With neither set (or 'enabled' false),
Parthinner.enabled is False and thin() should not be called.
"""

__author__ = "Stuart Illson"

import os
import random

from bluesky.exceptions import BlueSkyConfigurationError

from . import pardump_io

__all__ = [
    'Parthinner',
    'summarize_parinit',
]


class Parthinner():
    """Filters particles out of PARINIT files.

    Typical usage:

        p = Parthinner(self.config)
        if p.enabled:
            kept, total = p.thin(src, dest)

    thin() raises on malformed input or IO errors; callers are expected to
    catch and fall back to the unthinned source file so a bad PARINIT doesn't
    abort dispersion.
    """

    def __init__(self, config_getter):
        self._config_getter = config_getter
        self._enabled = bool(config_getter('parthin', 'enabled'))
        if not self._enabled:
            return

        self._min_mass_grams = config_getter('parthin', 'min_mass_grams')
        self._thin_bins = config_getter('parthin', 'thin_bins')
        self._validate_config()

        # A single RNG shared across all files in this run. Thinning is
        # intentionally non-reproducible between runs; each bsp invocation
        # seeds from system entropy.
        self._rng = random.Random()

    @property
    def enabled(self):
        return self._enabled

    def thin(self, src_path, dest_path):
        """Read src_path, drop particles per config, write to dest_path.

        Returns (kept, total).
        """
        header, particles = pardump_io.read_parinit(src_path)
        numpol = header[1]

        kept = [p for p in particles if self._keep(p, numpol)]
        pardump_io.write_parinit(dest_path, header, kept)

        return len(kept), len(particles)

    def _keep(self, particle, numpol):
        mass = pardump_io.particle_total_mass(particle[0], numpol)

        if self._min_mass_grams is not None:
            return mass >= self._min_mass_grams

        if self._thin_bins is not None:
            for upper, thin_rate in self._thin_bins:
                if mass < upper:
                    return self._rng.random() >= thin_rate
            return True

        return True

    def _validate_config(self):
        has_min = self._min_mass_grams is not None
        has_bins = self._thin_bins is not None

        if has_min and has_bins:
            raise BlueSkyConfigurationError(
                "parthin: 'min_mass_grams' and 'thin_bins' are mutually "
                "exclusive; set one or the other")

        if has_bins:
            self._validate_bins(self._thin_bins)

    @staticmethod
    def _validate_bins(bins):
        if not bins:
            raise BlueSkyConfigurationError(
                "parthin.thin_bins: must contain at least one "
                "[upper_mass, thin_rate] entry")

        prev_upper = None
        for entry in bins:
            try:
                upper, thin_rate = entry
            except (TypeError, ValueError):
                raise BlueSkyConfigurationError(
                    "parthin.thin_bins: each entry must be "
                    "[upper_mass, thin_rate], got %r" % (entry,))

            if prev_upper is not None and upper <= prev_upper:
                raise BlueSkyConfigurationError(
                    "parthin.thin_bins: upper bounds must be strictly "
                    "ascending (got %s after %s)" % (upper, prev_upper))

            if not (0.0 <= thin_rate <= 1.0):
                raise BlueSkyConfigurationError(
                    "parthin.thin_bins: thin_rate must be in [0, 1], got %s"
                    % thin_rate)

            prev_upper = upper


def summarize_parinit(path,
        mass_concentration_levels=(0.99, 0.95, 0.90, 0.80, 0.75),
        mass_thresholds_grams=(0.1, 1.0, 10.0, 100.0)):
    """Inspect a PARINIT file and return per-particle mass distribution stats.

    Useful for debugging and configuring parthin settings.
    The output tells you what fraction of particles carry the bulk of the mass, 
    and how much mass you would discard by thinning below various thresholds.

    Args:
     - path -- PARINIT file path
     - mass_concentration_levels -- mass-fraction targets. For each target f,
        the result reports the smallest number of particles (taken
        heaviest-first) whose cumulative mass is at least f of the total.
     - mass_thresholds_grams -- absolute mass thresholds in grams. For each
        threshold, the result reports the count of particles below it and the
        fraction of total mass they carry.

    Returns a dict:

        {
            'total_particles':    int,
            'total_mass_grams':   float,
            'mass_stats':         {'min','max','mean','median'} or None,
            'mass_concentration': {level: {'particles','fraction'}, ...},
            'particles_below':    {threshold: {'particles','fraction',
                                               'mass_fraction'}, ...},
        }
    """
    header, particles = pardump_io.read_parinit(path)
    numpol = header[1]
    masses = [pardump_io.particle_total_mass(p[0], numpol) for p in particles]

    n = len(masses)
    if n == 0:
        return {
            "total_particles": 0,
            "total_mass_grams": 0.0,
            "mass_stats": None,
            "mass_concentration": {level: {"particles": 0, "fraction": 0.0}
                for level in mass_concentration_levels},
            "particles_below": {threshold: {"particles": 0, "fraction": 0.0,
                "mass_fraction": 0.0} for threshold in mass_thresholds_grams},
        }

    total_mass = sum(masses)
    masses_asc = sorted(masses)
    masses_desc = list(reversed(masses_asc))

    # Mass concentration: walk heaviest-first, record the count that first
    # pushes cumulative mass past each target. Levels visited in ascending
    # order so a single pass suffices.
    mass_concentration = {}
    cumulative = 0.0
    i = 0
    for target in sorted(mass_concentration_levels):
        goal = target * total_mass
        while i < n and cumulative < goal:
            cumulative += masses_desc[i]
            i += 1
        mass_concentration[target] = {
            "particles": i,
            "fraction": i / n,
        }

    # Particles below each absolute threshold. Same ascending pass for all
    # thresholds, visited in ascending order.
    particles_below = {}
    count = 0
    mass_below = 0.0
    j = 0
    for threshold in sorted(mass_thresholds_grams):
        while j < n and masses_asc[j] < threshold:
            mass_below += masses_asc[j]
            count += 1
            j += 1
        particles_below[threshold] = {
            "particles": count,
            "fraction": count / n,
            "mass_fraction": mass_below / total_mass if total_mass else 0.0,
        }

    mid = n // 2
    median = (masses_asc[mid] if n % 2
        else (masses_asc[mid - 1] + masses_asc[mid]) / 2)

    return {
        "total_particles": n,
        "total_mass_grams": total_mass,
        "mass_stats": {
            "min": masses_asc[0],
            "max": masses_asc[-1],
            "mean": total_mass / n,
            "median": median,
        },
        "mass_concentration": mass_concentration,
        "particles_below": particles_below,
    }
