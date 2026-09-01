"""bluesky.loaders.rave

RAVE (Regional ABI-VIIRS Emissions) loader.

Two loader classes share one marshalling implementation:
  - NetcdfFileLoader: reads RAVE '.nc' files directly (lazy-imports xarray)
  - CsvFileLoader:    reads a pre-extracted CSV (no xarray)

Per the bluesky.loaders dispatch convention, the class name is
'<format.capitalize()><type.capitalize()>Loader', so
  {"format": "netcdf", "type": "file"} -> NetcdfFileLoader
  {"format": "CSV",    "type": "file"} -> CsvFileLoader

RAVE already provides emitted mass (PM25/CO, kg) and FRP/FRE, so this loader
injects ready-made emissions and bypasses the fuelbeds/consumption/emissions
compute chain.

Species scaling (config 'scaled', default False; NetCDF loader): read the larger
'PM25_scaled'/'CO_scaled' variants instead of the unscaled 'PM25'/'CO'.

Grouping (config 'group_by', default 'local'):
  - 'local' : (default) one fire per cell per LOCAL day (offset derived from
              longitude), to line up with FireSpider/FIS's local-day buckets. A
              local day spans two UTC days, so load the target UTC day plus its
              neighbour(s); a local day short by more than 'max_missing_hours'
              (default 5) of its 24 hours is dropped, with a visible warning
              naming any tolerated gaps.
  - 'utc'   : one fire per grid cell per UTC day. Needs only the single UTC day's
              files, but the day boundaries will not line up with FIS.
  See dev-private/docs/rave-data-and-loader.md.
"""


import datetime
import glob
import logging
import os

from bluesky.loaders import BaseLoader, BaseCsvFileLoader
from bluesky.exceptions import BlueSkyConfigurationError, BlueSkyGeographyValueError

__all__ = ["NetcdfFileLoader", "CsvFileLoader"]

# bluesky emissions are short tons; the HYSPLIT disperser multiplies by
# GRAMS_PER_TON (907184.74 g = 1 short ton) to get grams.
KG_PER_SHORT_TON = 907.18474
ACRES_PER_SQ_KM = 247.105
PHASE_FRACTIONS = {"flaming": 0.7, "smoldering": 0.2, "residual": 0.1}

# Named once so the config default and the bare-mixin fallback in _marshal cannot
# drift apart.
DEFAULT_GROUP_BY = "local"


def to_180(lon):
    """Normalize longitude to [-180, 180); idempotent on already-converted values."""
    return round(((float(lon) + 180.0) % 360.0) - 180.0, 10)


def utc_offset_hours(lng):
    """Approximate integer UTC offset from longitude (solar mean time)."""
    return int(round(float(lng) / 15.0))


def format_utc_offset(hours):
    """Format integer hour offset as '+HH:MM' / '-HH:MM'."""
    sign = "-" if hours < 0 else "+"
    return "{}{:02d}:00".format(sign, abs(int(hours)))


def kg_to_tons(kg):
    return float(kg) / KG_PER_SHORT_TON


def sq_km_to_acres(km2):
    return float(km2) * ACRES_PER_SQ_KM


def utc_date_str(iso):
    """'2026-01-01T00:00:00' -> '20260101'."""
    return datetime.datetime.fromisoformat(iso).strftime("%Y%m%d")


def np_time_to_iso(np_dt):
    """numpy.datetime64 -> 'YYYY-MM-DDTHH:MM:SS'."""
    return str(np_dt).split(".")[0][:19]


def local_date_str(iso, offset_h):
    """Local calendar date 'YYYYMMDD' for a UTC time at the given integer offset."""
    dt = datetime.datetime.fromisoformat(iso) + datetime.timedelta(hours=offset_h)
    return dt.strftime("%Y%m%d")


def normalize_date_str(val):
    """Coerces a config date to the 'YYYYMMDD' form used as the grouping key.

    Accepts None, a date/datetime, or a string. Note that Config's wildcard
    substitution turns a value that is purely a datetime into a datetime object
    (bluesky/config/__init__.py:126), so '{today:%Y%m%d}' arrives here already
    parsed -- hence accepting both.
    """
    if val is None:
        return None
    if isinstance(val, datetime.date):   # datetime.datetime is a subclass
        return val.strftime("%Y%m%d")
    s = str(val).strip()
    for fmt in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt).strftime("%Y%m%d")
        except ValueError:
            pass
    raise BlueSkyConfigurationError(
        "Invalid rave 'trim_to_date' value: {!r} (expected YYYYMMDD or"
        " YYYY-MM-DD)".format(val))


def required_utc_hours(local_date, offset_h):
    """The 24 UTC hour timestamps (ISO strings) whose local time falls on `local_date`
    ('YYYYMMDD') at the given integer offset. Used to test local-day completeness:
    local hour k (UTC = local - offset)."""
    d = datetime.datetime.strptime(local_date, "%Y%m%d")
    return [(d + datetime.timedelta(hours=k - offset_h)).strftime("%Y-%m-%dT%H:%M:%S")
            for k in range(24)]


def _warn_incomplete_coverage(gap_hours, n_kept, n_dropped, max_missing):
    """Very visible one-shot warning about incomplete hourly coverage in local mode."""
    bar = "!" * 72
    logging.warning(
        "\n%s\nRAVE local-day grouping: INCOMPLETE HOURLY COVERAGE\n"
        "  Missing UTC hourly file(s) tolerated in kept days: %s\n"
        "  Kept %d cell-day(s) with <= %d missing hour(s).\n"
        "  Dropped %d cell-day(s) exceeding max_missing_hours=%d "
        "(likely boundary days — load the neighbouring UTC day(s) to fill them).\n%s",
        bar,
        ", ".join(sorted(gap_hours)) or "(none; all incomplete days exceeded tolerance)",
        n_kept, max_missing, n_dropped, max_missing, bar)


def _warn_multiple_local_days(fires):
    """Warns when one local-grouped load emits more than one local day.

    The neighbouring UTC day(s) needed to complete the target local day also
    carry enough hours to complete a neighbouring LOCAL day -- the day before for
    western cells, the day after for eastern ones -- so a D-1..D+1 load yields
    two days per cell. That is correct for a deliberate multi-day load and a
    silent doubling for a scheduled daily one, and nothing else distinguishes
    the two, so say so rather than guessing. Suppressed when 'trim_to_date' is
    set, since that says the choice was made on purpose.
    """
    days = sorted({f["id"].split("-")[1] for f in fires})
    if len(days) < 2:
        return
    counts = {d: sum(1 for f in fires if f["id"].split("-")[1] == d) for d in days}
    bar = "!" * 72
    logging.warning(
        "\n%s\nRAVE local-day grouping: %d LOCAL DAYS EMITTED FROM ONE LOAD\n"
        "  %s\n"
        "  Loading the neighbouring UTC day(s) also completes neighbouring local\n"
        "  day(s), so a single target day's load emits more than one day.\n"
        "  Intentional for a multi-day load; for a single-day run set\n"
        "  'trim_to_date' (e.g. '{today-1:%%Y%%m%%d}') to keep just the one.\n%s",
        bar, len(days),
        ", ".join("%s: %d fire(s)" % (d, counts[d]) for d in days),
        bar)


class _RaveMarshalMixin:
    """Turns flat cell-hour records into one Fire per grid cell."""

    def _setup_country_lookup(self, config):
        if not config.get("assign_country", True):
            return None
        from bluesky.countries.lookup import CountryLookup, get_default_lookup
        shapefile = config.get("country_shapefile")
        return CountryLookup(shapefile) if shapefile else get_default_lookup()

    def _setup_grouping(self, config):
        # "local" (default) = one fire per cell per LOCAL day, dropping days whose
        # UTC-hour coverage is short by more than max_missing_hours; matches the
        # local-day buckets FireSpider/FIS use, at the cost of needing the
        # neighbouring UTC day(s) loaded. "utc" = one fire per cell per UTC day.
        # See dev-private/docs/rave-data-and-loader.md.
        self._group_by = config.get("group_by", DEFAULT_GROUP_BY)
        self._max_missing_hours = config.get("max_missing_hours", 5)
        self._loaded_hours = set()   # UTC hour ISO strings actually loaded
        # Optional single day to keep. Local grouping needs the neighbouring UTC
        # day(s) loaded, and those extra hours are enough to also complete a
        # neighbouring LOCAL day -- D-1 for western cells, D+1 for eastern ones --
        # so a D-1..D+1 load emits two days per cell unless this is set.
        self._trim_to_date = normalize_date_str(config.get("trim_to_date"))

    def _lookup_country(self, lat, lng):
        lookup = getattr(self, "_country_lookup", None)
        if lookup is None:
            return None
        try:
            return lookup.lookup(lat, lng)
        except BlueSkyGeographyValueError:
            # a single out-of-range point must not fail the whole load;
            # systematic failures (e.g. a missing shapefile) surface instead.
            return None

    def _marshal(self, records):
        group_by = getattr(self, "_group_by", DEFAULT_GROUP_BY)
        groups = {}
        for r in records:
            if group_by == "local":
                date_key = local_date_str(r["time"], utc_offset_hours(r["lng"]))
            else:
                date_key = utc_date_str(r["time"])
            groups.setdefault((r["row"], r["col"], date_key), []).append(r)

        groups = self._trim_groups_to_date(groups)

        if group_by == "local":
            return self._marshal_local(groups)

        fires = []
        for key, recs in groups.items():
            fire = self._build_fire(key, recs)
            if fire is not None:
                fires.append(fire)
        return fires

    def _trim_groups_to_date(self, groups):
        """Keeps only the groups on the configured 'trim_to_date', if set.

        Applied after grouping but before the completeness check, so that a
        neighbouring day loaded only to complete the target day is never built
        into a fire and never reported as a dropped cell-day. The date compared
        is the group's own key: the LOCAL day under group_by 'local', the UTC day
        under 'utc'.
        """
        target = getattr(self, "_trim_to_date", None)
        if not target:
            return groups

        trimmed = {k: v for k, v in groups.items() if k[2] == target}
        dropped = len(groups) - len(trimmed)
        if dropped:
            logging.info("RAVE trim_to_date=%s: kept %d cell-day(s), dropped %d"
                " on neighbouring day(s)", target, len(trimmed), dropped)
        if not trimmed and groups:
            logging.warning("RAVE trim_to_date=%s matched none of the %d loaded"
                " cell-day(s) (%s) - check that the date is covered by the files"
                " loaded", target, len(groups),
                ", ".join(sorted({k[2] for k in groups})))
        return trimmed

    def _marshal_local(self, groups):
        """Local-day grouping: emit only local days whose UTC-hour coverage is complete
        enough (at most `max_missing_hours` of the day's 24 hours absent), warning once
        about any tolerated gaps. Coverage is measured against the set of UTC hours the
        loader actually loaded, so an hour with no fire still counts as covered."""
        loaded_hours = getattr(self, "_loaded_hours", set())
        max_missing = getattr(self, "_max_missing_hours", 5)
        fires = []
        gap_hours = set()
        n_kept_with_gaps = 0
        n_dropped = 0
        for key, recs in groups.items():
            local_date = key[2]
            offset_h = utc_offset_hours(recs[0]["lng"])
            missing = [h for h in required_utc_hours(local_date, offset_h)
                       if h not in loaded_hours]
            if len(missing) > max_missing:
                n_dropped += 1
                continue
            fire = self._build_fire(key, recs)
            if fire is None:
                continue
            if missing:
                gap_hours.update(missing)
                n_kept_with_gaps += 1
            fires.append(fire)
        if n_kept_with_gaps or n_dropped:
            _warn_incomplete_coverage(gap_hours, n_kept_with_gaps, n_dropped, max_missing)
        if not getattr(self, "_trim_to_date", None):
            _warn_multiple_local_days(fires)
        return fires

    def _build_fire(self, key, recs):
        row, col, date_str = key
        lat, lng = recs[0]["lat"], recs[0]["lng"]

        total_pm25_kg = sum(r["pm25_kg"] for r in recs)
        if total_pm25_kg <= 0:
            return None
        total_co_kg = sum(r["co_kg"] for r in recs)
        pm25_tons = kg_to_tons(total_pm25_kg)
        co_tons = kg_to_tons(total_co_kg)

        offset_h = utc_offset_hours(lng)
        offset = datetime.timedelta(hours=offset_h)
        offset_str = format_utc_offset(offset_h)

        timeprofile = {}
        local_times = []
        for r in recs:
            local_dt = datetime.datetime.fromisoformat(r["time"]) + offset
            local_times.append(local_dt)
            frac = r["pm25_kg"] / total_pm25_kg
            timeprofile[local_dt.strftime("%Y-%m-%dT%H:%M:%S")] = {
                "area_fraction": frac, "flaming": frac,
                "smoldering": frac, "residual": frac,
            }

        start = min(local_times)
        end = start + datetime.timedelta(hours=24)
        frp = max(r["frp_mw"] for r in recs)  # peak (max) daily FRP for the cell

        emissions = {
            phase: {"PM2.5": [pm25_tons * f], "CO": [co_tons * f]}
            for phase, f in PHASE_FRACTIONS.items()
        }
        # The phases sum to 1.0, so the per-fuelbed 'total' is just the undivided
        # tons. Dispersion reads the phases directly, but the extra-file writers
        # (emissionscsv, smokeready) read this 'total'; without it they send every
        # fire to failed_fires.
        emissions["total"] = {"PM2.5": [pm25_tons], "CO": [co_tons]}
        point = {
            "lat": lat,
            "lng": lng,
            "area": sq_km_to_acres(recs[0]["area_km2"]),
            "utc_offset": offset_str,
            "frp": frp,
            "consumption": {"summary": {
                "flaming": [0.0], "smoldering": [0.0],
                "residual": [0.0], "total": [0.0]}},
            "fuelbeds": [{"emissions": emissions}],
            "emissions": {"summary": {
                "PM2.5": pm25_tons, "CO": co_tons,
                "total": pm25_tons + co_tons}},
        }
        active_area = {
            "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%S"),
            "utc_offset": offset_str,
            "timeprofile": timeprofile,
            "specified_points": [point],
        }
        country = self._lookup_country(lat, lng)
        if country:
            active_area["country"] = country
        return {
            "id": "rave-{}-{}-{}".format(date_str, row, col),
            "type": "wf",
            "activity": [{"active_areas": [active_area]}],
        }


class NetcdfFileLoader(_RaveMarshalMixin, BaseLoader):
    """Loads RAVE data directly from '.nc' files (lazy-imports xarray)."""

    DEFAULT_PATTERN = "*.nc"

    # Inherits BaseLoader (NOT BaseFileLoader) so it is not bound to a single
    # 'file'; it resolves a directory/glob/list itself.
    def __init__(self, **config):
        super().__init__(**config)
        self._filenames = self._resolve_files(config)
        self._scaled = config.get("scaled", False)   # read PM25_scaled/CO_scaled
        self._min_qa = config.get("min_qa", 1)
        self._country_lookup = self._setup_country_lookup(config)
        self._setup_grouping(config)

    def _resolve_files(self, config):
        if config.get("files"):
            return sorted(config["files"])
        if config.get("dir"):
            return self._resolve_dir_files(config)
        if config.get("file"):
            return [config["file"]]
        raise BlueSkyConfigurationError(
            "rave NetCDF loader requires 'files', 'dir', or 'file'")

    def _resolve_dir_files(self, config):
        """Globs 'dir' with one or more 'pattern's, de-duplicated.

        'pattern' may be a list, so that one load can span sibling directories
        without pulling in everything under them. RAVE is archived as
        '<root>/<YYYY>/<MM>/', and a local day needs the neighbouring UTC day(s)
        (see 'group_by'), which cross the month -- and on Jan 1 the year --
        boundary. A pattern may contain directory components, and each entry
        resolves its own '{today+/-N:...}' wildcards before reaching here, so a
        single static config covers every date of the year:

            "dir": "/data/.../RAVE-HrlyEmiss-3km",
            "pattern": [
                "{today-1:%Y}/{today-1:%m}/*_s{today-1:%Y%m%d}*.nc",
                "{today:%Y}/{today:%m}/*_s{today:%Y%m%d}*.nc",
                "{today+1:%Y}/{today+1:%m}/*_s{today+1:%Y%m%d}*.nc"
            ]

        An individual pattern matching nothing is NOT an error: on a forecast run
        the D+1 files may not have landed yet, and local-day completeness
        ('max_missing_hours') is what decides whether that matters. Matching
        nothing at all is an error, since that only happens when the path is
        wrong -- previously it returned [] and the run went on to load zero
        fires without complaint.
        """
        patterns = config.get("pattern", self.DEFAULT_PATTERN)
        if isinstance(patterns, str):
            patterns = [patterns]

        filenames = set()
        for p in patterns:
            matched = glob.glob(os.path.join(config["dir"], p))
            logging.debug("rave: pattern %r matched %d file(s)", p, len(matched))
            filenames.update(matched)

        if not filenames:
            raise BlueSkyConfigurationError(
                "rave NetCDF loader matched no files under '{}' with pattern(s)"
                " {}".format(config["dir"], patterns))

        return sorted(filenames)

    def _load(self):
        try:
            import xarray
        except ImportError:
            raise BlueSkyConfigurationError(
                "The rave NetCDF loader requires xarray and netCDF4. "
                "Install them with: pip install xarray netCDF4")
        records = []
        for path in self._filenames:
            records.extend(self._extract_records(xarray, path))
        return records

    def _extract_records(self, xarray, path):
        import numpy
        ds = xarray.open_dataset(path)
        try:
            pm_var = "PM25_scaled" if self._scaled else "PM25"
            co_var = "CO_scaled" if self._scaled else "CO"
            pm25 = ds[pm_var].values[0]          # (grid_yt, grid_xt)
            rows, cols = numpy.where(numpy.isfinite(pm25))
            time_str = np_time_to_iso(ds["time"].values[0])
            self._loaded_hours.add(time_str)   # covered even if this hour has no fires
            lat = ds["grid_latt"].values
            lon = ds["grid_lont"].values
            area = ds["area"].values
            co = ds[co_var].values[0]
            frp = ds["FRP_MEAN"].values[0]
            fre = ds["FRE"].values[0]
            qa = ds["QA"].values[0]

            out = []
            for r, c in zip(rows.tolist(), cols.tolist()):
                q = int(qa[r, c])
                if q < self._min_qa:
                    continue
                out.append({
                    "time": time_str,
                    "lat": float(lat[r, c]),
                    "lng": to_180(lon[r, c]),
                    "area_km2": float(area[r, c]),
                    "pm25_kg": float(pm25[r, c]),
                    "co_kg": float(co[r, c]),
                    "frp_mw": float(frp[r, c]),
                    "fre_mj": float(fre[r, c]),
                    "qa": q,
                    "row": r,
                    "col": c,
                })
            return out
        finally:
            ds.close()


class CsvFileLoader(_RaveMarshalMixin, BaseCsvFileLoader):
    """Loads RAVE data from a pre-extracted CSV (one row per fire cell-hour)."""

    def __init__(self, **config):
        super().__init__(**config)
        self._min_qa = config.get("min_qa", 1)
        self._country_lookup = self._setup_country_lookup(config)
        self._setup_grouping(config)

    def _load(self):
        rows = super()._load()  # pyairfire CSV2JSON -> list of row dicts
        records = [self._row_to_record(r) for r in rows]
        self._loaded_hours = {rec["time"] for rec in records}
        return [rec for rec in records if rec["qa"] >= self._min_qa]

    def _row_to_record(self, row):
        return {
            "time": row["time"],
            "lat": float(row["lat"]),
            "lng": to_180(row["lon"]),
            "area_km2": float(row["area_km2"]),
            "pm25_kg": float(row["PM25"]),
            "co_kg": float(row.get("CO") or 0.0),
            "frp_mw": float(row.get("FRP_MEAN") or 0.0),
            "fre_mj": float(row.get("FRE") or 0.0),
            "qa": int(float(row.get("QA") or 1)),
            "row": int(row["row"]),
            "col": int(row["col"]),
        }
