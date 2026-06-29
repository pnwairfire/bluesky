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
"""


import datetime
import glob
import os

from bluesky.loaders import BaseLoader, BaseCsvFileLoader
from bluesky.exceptions import BlueSkyConfigurationError

__all__ = ["NetcdfFileLoader", "CsvFileLoader"]

# bluesky emissions are short tons; the HYSPLIT disperser multiplies by
# GRAMS_PER_TON (907184.74 g = 1 short ton) to get grams.
KG_PER_SHORT_TON = 907.18474
ACRES_PER_SQ_KM = 247.105
PHASE_FRACTIONS = {"flaming": 0.7, "smoldering": 0.2, "residual": 0.1}


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


class _RaveMarshalMixin:
    """Turns flat cell-hour records into one Fire per grid cell."""

    def _load_country_grid(self, config):
        path = config.get("country_lookup")
        if not path:
            return None
        import numpy
        return numpy.load(path, mmap_mode="r")  # near-zero resident; O(1) lookups

    def _lookup_country(self, row, col):
        grid = getattr(self, "_country_grid", None)
        if grid is None:
            return None
        if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
            return str(grid[row, col]) or None
        return None

    def _marshal(self, records):
        groups = {}
        for r in records:
            key = (r["row"], r["col"], utc_date_str(r["time"]))
            groups.setdefault(key, []).append(r)

        fires = []
        for key, recs in groups.items():
            fire = self._build_fire(key, recs)
            if fire is not None:
                fires.append(fire)
        return fires

    def _build_fire(self, key, recs):
        row, col, utcdate = key
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
        frp = sum(r["frp_mw"] for r in recs) / len(recs)  # representative for SEV

        emissions = {
            phase: {"PM2.5": [pm25_tons * f], "CO": [co_tons * f]}
            for phase, f in PHASE_FRACTIONS.items()
        }
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
        country = self._lookup_country(row, col)
        if country:
            active_area["country"] = country
        return {
            "id": "rave-{}-{}-{}".format(utcdate, row, col),
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
        self._min_qa = config.get("min_qa", 1)
        self._country_grid = self._load_country_grid(config)

    def _resolve_files(self, config):
        if config.get("files"):
            return sorted(config["files"])
        if config.get("dir"):
            pattern = config.get("pattern", self.DEFAULT_PATTERN)
            return sorted(glob.glob(os.path.join(config["dir"], pattern)))
        if config.get("file"):
            return [config["file"]]
        raise BlueSkyConfigurationError(
            "rave NetCDF loader requires 'files', 'dir', or 'file'")

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
            pm25 = ds["PM25"].values[0]          # (grid_yt, grid_xt)
            rows, cols = numpy.where(numpy.isfinite(pm25))
            time_str = np_time_to_iso(ds["time"].values[0])
            lat = ds["grid_latt"].values
            lon = ds["grid_lont"].values
            area = ds["area"].values
            co = ds["CO"].values[0]
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
        self._country_grid = self._load_country_grid(config)

    def _load(self):
        rows = super()._load()  # pyairfire CSV2JSON -> list of row dicts
        records = [self._row_to_record(r) for r in rows]
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
