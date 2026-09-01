"""Unit tests for the RAVE loader (bluesky.loaders.rave).

Covers the pure helpers, the record->Fire marshalling, file resolution, the CSV
loader, dispatch, and default-on country assignment. These need no NetCDF sample
data or xarray; the CSV cases use the small fixture in data/rave-input.csv.
(NetCDF-extraction tests that require the multi-MB .nc sample live in the
project's private test area.)
"""

import datetime
import logging
import os

import numpy as np
from pytest import fixture, raises

from bluesky.loaders import rave
from bluesky.datetimeutils import parse_datetime
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.models.fires import FiresManager
from bluesky.config import Config
from bluesky.modules import load as load_module
from bluesky.countries.lookup import DEFAULT_COUNTRIES_SHAPEFILE

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_FIXTURE = os.path.join(DATA_DIR, "rave-input.csv")


@fixture(autouse=True)
def _reset_config():
    """Reset the Config singleton around every test to prevent state leaks."""
    Config().reset()
    yield
    Config().reset()


## Pure helpers

def test_to_180():
    assert rave.to_180(269.595) == -90.405          # 0..360 -> -180..180
    assert round(rave.to_180(332.16), 2) == -27.84
    assert rave.to_180(-90.405) == -90.405          # idempotent on already-converted


def test_utc_offset_hours():
    assert rave.utc_offset_hours(-120.0) == -8
    assert rave.utc_offset_hours(-90.405) == -6
    assert rave.utc_offset_hours(0.0) == 0


def test_format_utc_offset():
    assert rave.format_utc_offset(-8) == "-08:00"
    assert rave.format_utc_offset(0) == "+00:00"
    assert rave.format_utc_offset(5) == "+05:00"


def test_unit_conversions():
    assert rave.kg_to_tons(907.18474) == 1.0        # 1 short ton
    assert round(rave.sq_km_to_acres(9.0), 3) == 2223.945


def test_time_helpers():
    assert rave.utc_date_str("2026-01-01T00:00:00") == "20260101"
    assert rave.np_time_to_iso(np.datetime64("2026-01-01T00:00:00.000000000")) \
        == "2026-01-01T00:00:00"


## Marshalling (records -> Fires)

def _utc_mixin():
    """A marshaller pinned to 'utc' grouping.

    The cases below assert UTC-day-keyed ids and 1-2 hour fixtures, so they are
    inherently utc-mode tests. 'local' is the loader default (DEFAULT_GROUP_BY), so
    they opt in explicitly rather than relying on whatever the default happens to be.
    """
    m = rave._RaveMarshalMixin()
    m._setup_grouping({"group_by": "utc"})
    return m


def _records_two_cells():
    # Cell A: row100/col200, lng -120 (offset -8), two hours; pm25 1t + 3t = 4t
    # Cell B: row100/col300, lng -90 (offset -6), one hour; pm25 1t
    KG = rave.KG_PER_SHORT_TON
    return [
        {"time": "2026-01-01T00:00:00", "lat": 40.0, "lng": -120.0, "area_km2": 9.0,
         "pm25_kg": 1 * KG, "co_kg": 2 * KG, "frp_mw": 100.0, "fre_mj": 3.6e5,
         "qa": 3, "row": 100, "col": 200},
        {"time": "2026-01-01T01:00:00", "lat": 40.0, "lng": -120.0, "area_km2": 9.0,
         "pm25_kg": 3 * KG, "co_kg": 6 * KG, "frp_mw": 200.0, "fre_mj": 5.4e5,
         "qa": 3, "row": 100, "col": 200},
        {"time": "2026-01-01T00:00:00", "lat": 40.0, "lng": -90.0, "area_km2": 9.0,
         "pm25_kg": 1 * KG, "co_kg": 1 * KG, "frp_mw": 50.0, "fre_mj": 1.8e5,
         "qa": 2, "row": 100, "col": 300},
    ]


def test_marshal_one_fire_per_cell():
    fires = _utc_mixin()._marshal(_records_two_cells())
    assert len(fires) == 2
    ids = sorted(f["id"] for f in fires)
    assert ids == ["rave-20260101-100-200", "rave-20260101-100-300"]
    assert all(f["type"] == "wf" for f in fires)


def test_marshal_cell_a_structure():
    fires = {f["id"]: f for f in _utc_mixin()._marshal(_records_two_cells())}
    a = fires["rave-20260101-100-200"]
    aa = a["activity"][0]["active_areas"][0]
    assert aa["utc_offset"] == "-08:00"
    assert aa["start"] == "2025-12-31T16:00:00"     # local of first UTC hour
    assert aa["end"] == "2026-01-01T16:00:00"       # start + 24h

    pt = aa["specified_points"][0]
    assert pt["lat"] == 40.0 and pt["lng"] == -120.0
    assert round(pt["area"], 3) == 2223.945         # 9 km2 -> acres
    assert pt["frp"] == 200.0                        # max of 100, 200
    assert pt["consumption"]["summary"]["total"] == [0.0]

    # daily totals in SHORT TONS, split 70/20/10
    em = pt["fuelbeds"][0]["emissions"]
    assert em["flaming"]["PM2.5"] == [2.8] and em["smoldering"]["PM2.5"] == [0.8]
    assert em["residual"]["PM2.5"] == [0.4]
    assert em["flaming"]["CO"] == [5.6]
    # per-fuelbed 'total' = sum across phases; read by the extra-file writers
    assert em["total"]["PM2.5"] == [4.0] and em["total"]["CO"] == [8.0]
    assert pt["emissions"]["summary"]["PM2.5"] == 4.0
    assert pt["emissions"]["summary"]["CO"] == 8.0


def test_marshal_timeprofile_local_and_sums_to_one():
    fires = {f["id"]: f for f in _utc_mixin()._marshal(_records_two_cells())}
    tp = fires["rave-20260101-100-200"]["activity"][0]["active_areas"][0]["timeprofile"]
    assert set(tp.keys()) == {"2025-12-31T16:00:00", "2025-12-31T17:00:00"}
    assert tp["2025-12-31T16:00:00"]["flaming"] == 0.25   # 1t / 4t
    assert tp["2025-12-31T17:00:00"]["flaming"] == 0.75   # 3t / 4t
    for entry in tp.values():
        assert set(entry) == {"area_fraction", "flaming", "smoldering", "residual"}
    assert round(sum(e["area_fraction"] for e in tp.values()), 9) == 1.0


def test_marshal_lossless_hourly_reconstruction():
    # Sum_phase timeprofile[h][phase] * emissions[phase][PM2.5] == original hourly tons
    fires = {f["id"]: f for f in _utc_mixin()._marshal(_records_two_cells())}
    aa = fires["rave-20260101-100-200"]["activity"][0]["active_areas"][0]
    em = aa["specified_points"][0]["fuelbeds"][0]["emissions"]
    h16 = aa["timeprofile"]["2025-12-31T16:00:00"]
    reconstructed = sum(h16[p] * em[p]["PM2.5"][0] for p in rave.PHASE_FRACTIONS)
    assert round(reconstructed, 9) == 1.0                 # hour 1 was 1 short ton


def test_marshal_skips_zero_emission_cell():
    recs = [{"time": "2026-01-01T00:00:00", "lat": 1.0, "lng": 1.0, "area_km2": 9.0,
             "pm25_kg": 0.0, "co_kg": 0.0, "frp_mw": 0.0, "fre_mj": 0.0,
             "qa": 3, "row": 1, "col": 1}]
    assert _utc_mixin()._marshal(recs) == []


## trim_to_date (keep only the target day out of a multi-day load)

def _three_utc_days_loaded():
    loaded = set()
    for d in ("20260731", "20260801", "20260802"):
        base = datetime.datetime.strptime(d, "%Y%m%d")
        for h in range(24):
            loaded.add((base + datetime.timedelta(hours=h)).strftime("%Y-%m-%dT%H:%M:%S"))
    return loaded


def _cell_records(loaded, lng, row=100, col=200):
    return [{"time": t, "lat": 40.0, "lng": lng, "area_km2": 9.0,
             "pm25_kg": rave.KG_PER_SHORT_TON, "co_kg": 0.0, "frp_mw": 1.0,
             "fre_mj": 0.0, "qa": 3, "row": row, "col": col}
            for t in sorted(loaded)]


def _local_days(mixin, records):
    return sorted(f["id"].split("-")[1] for f in mixin._marshal(records))


def _mixin(loaded, **cfg):
    cfg.setdefault("group_by", "local")
    m = rave._RaveMarshalMixin()
    m._setup_grouping(cfg)
    m._loaded_hours = loaded
    return m


def test_without_trim_a_three_day_load_emits_neighbouring_local_days():
    # the behavior trim_to_date exists to suppress: the neighbouring UTC days
    # loaded to complete local D also complete a neighbouring LOCAL day, and
    # which one depends on the sign of the cell's offset
    loaded = _three_utc_days_loaded()
    assert _local_days(_mixin(loaded), _cell_records(loaded, -120.0)) \
        == ["20260731", "20260801"]                    # western: D-1 and D
    assert _local_days(_mixin(loaded), _cell_records(loaded, 150.0)) \
        == ["20260801", "20260802"]                    # eastern: D and D+1


def test_trim_to_date_keeps_only_the_target_local_day():
    loaded = _three_utc_days_loaded()
    for lng in (-120.0, 150.0):
        m = _mixin(loaded, trim_to_date="20260801")
        assert _local_days(m, _cell_records(loaded, lng)) == ["20260801"]


def test_trim_to_date_accepts_dashed_and_datetime_forms():
    # Config wildcard substitution turns a pure datetime string into a datetime
    # object, so the loader has to accept that too
    loaded = _three_utc_days_loaded()
    for val in ("2026-08-01", datetime.datetime(2026, 8, 1), datetime.date(2026, 8, 1)):
        m = _mixin(loaded, trim_to_date=val)
        assert _local_days(m, _cell_records(loaded, -120.0)) == ["20260801"]


def test_trim_to_date_rejects_garbage():
    with raises(BlueSkyConfigurationError):
        _mixin(set(), trim_to_date="not-a-date")


def test_trim_to_date_applies_to_utc_grouping_too():
    loaded = _three_utc_days_loaded()
    m = _mixin(loaded, group_by="utc", trim_to_date="20260801")
    assert _local_days(m, _cell_records(loaded, -120.0)) == ["20260801"]


def test_no_trim_by_default():
    loaded = _three_utc_days_loaded()
    assert _mixin(loaded)._trim_to_date is None


def test_warns_when_more_than_one_local_day_is_emitted(caplog):
    loaded = _three_utc_days_loaded()
    m = _mixin(loaded)
    recs = _cell_records(loaded, -120.0, col=200) + _cell_records(loaded, 150.0, col=300)
    with caplog.at_level(logging.WARNING):
        m._marshal(recs)
    msgs = [r.getMessage() for r in caplog.records]
    assert any("LOCAL DAYS EMITTED FROM ONE LOAD" in m_ for m_ in msgs)
    # names the days and points at the option that suppresses it
    warning = next(m_ for m_ in msgs if "LOCAL DAYS EMITTED" in m_)
    for day in ("20260731", "20260801", "20260802"):
        assert day in warning
    assert "trim_to_date" in warning


def test_no_multi_day_warning_when_trim_to_date_is_set(caplog):
    loaded = _three_utc_days_loaded()
    m = _mixin(loaded, trim_to_date="20260801")
    with caplog.at_level(logging.WARNING):
        m._marshal(_cell_records(loaded, -120.0))
    assert not any("LOCAL DAYS EMITTED" in r.getMessage() for r in caplog.records)


def test_no_multi_day_warning_for_a_single_local_day(caplog):
    # only the target day's hours loaded -> one day out -> nothing to warn about
    loaded = set(rave.required_utc_hours("20260801", -8))
    m = _mixin(loaded)
    with caplog.at_level(logging.WARNING):
        fires = m._marshal(_cell_records(loaded, -120.0))
    assert _local_days(m, _cell_records(loaded, -120.0)) == ["20260801"]
    assert not any("LOCAL DAYS EMITTED" in r.getMessage() for r in caplog.records)


## Local-day grouping (the default; see DEFAULT_GROUP_BY)

def _local_mixin(loaded_hours, max_missing_hours=5):
    """A marshaller in local mode that believes `loaded_hours` were loaded.

    Completeness is measured against the UTC hours the loader actually read, not
    against the records, so an hour whose file was loaded but held no fire in this
    cell still counts as covered.
    """
    m = rave._RaveMarshalMixin()
    m._setup_grouping({"group_by": "local", "max_missing_hours": max_missing_hours})
    m._loaded_hours = set(loaded_hours)
    return m


# lng -120 -> offset -8, so UTC 2026-01-01T02:00 is local 2025-12-31T18:00:
# the record's UTC day (20260101) and local day (20251231) deliberately differ.
LOCAL_DAY = "20251231"
LOCAL_DAY_OFFSET = -8
LOCAL_DAY_UTC_HOURS = rave.required_utc_hours(LOCAL_DAY, LOCAL_DAY_OFFSET)


def _straddling_record():
    return {"time": "2026-01-01T02:00:00", "lat": 40.0, "lng": -120.0,
            "area_km2": 9.0, "pm25_kg": rave.KG_PER_SHORT_TON, "co_kg": 0.0,
            "frp_mw": 10.0, "fre_mj": 0.0, "qa": 3, "row": 100, "col": 200}


def test_group_by_defaults_to_local():
    assert rave.DEFAULT_GROUP_BY == "local"
    loader = rave.NetcdfFileLoader(
        name="rave", format="netcdf", type="file", file="x.nc")
    assert loader._group_by == "local"


def test_local_grouping_keys_by_local_day_not_utc_day():
    m = _local_mixin(LOCAL_DAY_UTC_HOURS)
    fires = m._marshal([_straddling_record()])
    # utc grouping would have keyed this record's fire "rave-20260101-100-200"
    assert [f["id"] for f in fires] == ["rave-20251231-100-200"]


def test_local_grouping_drops_day_missing_too_many_hours():
    # 6 of the 24 required UTC hours never loaded, over the default tolerance of 5
    m = _local_mixin(LOCAL_DAY_UTC_HOURS[:18])
    assert m._marshal([_straddling_record()]) == []


def test_local_grouping_keeps_day_within_missing_tolerance():
    # 4 missing, within tolerance -> kept (with a warning)
    m = _local_mixin(LOCAL_DAY_UTC_HOURS[:20])
    assert [f["id"] for f in m._marshal([_straddling_record()])] \
        == ["rave-20251231-100-200"]


def test_local_grouping_counts_loaded_hours_without_fire_as_covered():
    # one record, but all 24 hourly files loaded -> complete, nothing dropped
    m = _local_mixin(LOCAL_DAY_UTC_HOURS)
    assert len(m._marshal([_straddling_record()])) == 1
    # same single record, no hours declared loaded -> all 24 missing -> dropped
    assert _local_mixin(set())._marshal([_straddling_record()]) == []


## File resolution: 'dir' + 'pattern' (single and multi)

def _rave_archive(tmp_path):
    """A '<root>/<YYYY>/<MM>/' RAVE archive spanning a month boundary."""
    root = tmp_path / "RAVE-HrlyEmiss-3km"
    for ym, days in (("2026/07", ("20260731",)), ("2026/08", ("20260801", "20260802"))):
        d = root / ym
        d.mkdir(parents=True, exist_ok=True)
        for day in days:
            for hour in ("00", "01"):
                (d / ("RAVE-HrlyEmiss-3km_v2r0_blend_s{}{}00000_e{}{}59590"
                      "_c{}{}3045.nc".format(day, hour, day, hour, day, hour))).touch()
    return root


def _days_resolved(filenames):
    return sorted({os.path.basename(f).split("_blend_s")[1][:8] for f in filenames})


def _resolve(**config):
    loader = rave.NetcdfFileLoader.__new__(rave.NetcdfFileLoader)
    return loader._resolve_files(config)


def test_resolve_files_dir_with_string_pattern(tmp_path):
    root = _rave_archive(tmp_path)
    files = _resolve(dir=str(root / "2026/07"), pattern="*.nc")
    assert _days_resolved(files) == ["20260731"]


def test_resolve_files_dir_pattern_may_contain_subdirs(tmp_path):
    # os.path.join(dir, pattern) means a pattern can reach into child dirs
    root = _rave_archive(tmp_path)
    files = _resolve(dir=str(root), pattern="2026/*/*.nc")
    assert _days_resolved(files) == ["20260731", "20260801", "20260802"]


def test_resolve_files_dir_pattern_list_spans_month_boundary(tmp_path):
    # the D-1/D/D+1 window a local day needs, on the 1st of a month, without
    # dragging in the rest of either month
    root = _rave_archive(tmp_path)
    files = _resolve(dir=str(root), pattern=[
        "2026/07/*_s20260731*.nc",
        "2026/08/*_s20260801*.nc",
        "2026/08/*_s20260802*.nc",
    ])
    assert _days_resolved(files) == ["20260731", "20260801", "20260802"]
    assert len(files) == 6


def test_resolve_files_dir_pattern_list_dedupes_and_sorts(tmp_path):
    root = _rave_archive(tmp_path)
    files = _resolve(dir=str(root), pattern=["2026/*/*.nc", "2026/08/*.nc"])
    assert len(files) == len(set(files)) == 6
    assert files == sorted(files)


def test_resolve_files_dir_tolerates_a_pattern_matching_nothing(tmp_path):
    # a forecast run's D+1 files may not have landed yet; that is for
    # local-day completeness to judge, not a configuration error
    root = _rave_archive(tmp_path)
    files = _resolve(dir=str(root), pattern=[
        "2026/08/*_s20260801*.nc",
        "2026/08/*_s20260803*.nc",   # not delivered yet
    ])
    assert _days_resolved(files) == ["20260801"]


def test_resolve_files_dir_raises_when_nothing_matches(tmp_path):
    root = _rave_archive(tmp_path)
    with raises(BlueSkyConfigurationError):
        _resolve(dir=str(root), pattern=["2026/09/*.nc"])


## File resolution (NetcdfFileLoader, no file opened)

def test_resolve_files_explicit_list():
    loader = rave.NetcdfFileLoader(name="rave", format="netcdf", type="file",
                                   files=["/b.nc", "/a.nc"])
    assert loader._filenames == ["/a.nc", "/b.nc"]  # sorted


def test_resolve_files_single():
    loader = rave.NetcdfFileLoader(name="rave", format="netcdf", type="file",
                                   file="/only.nc")
    assert loader._filenames == ["/only.nc"]


def test_resolve_files_requires_input():
    with raises(BlueSkyConfigurationError):
        rave.NetcdfFileLoader(name="rave", format="netcdf", type="file")


## CSV loader (uses the small fixture)

def test_csv_loader_end_to_end():
    loader = rave.CsvFileLoader(
        name="rave", format="CSV", type="file", file=CSV_FIXTURE, group_by="utc")
    fires = {f["id"]: f for f in loader.load()}
    assert set(fires) == {"rave-20260101-100-200", "rave-20260101-100-300"}

    aa = fires["rave-20260101-100-200"]["activity"][0]["active_areas"][0]
    # load() casts to Fire and parses start/end into datetimes via _prune_activity
    assert aa["start"] == parse_datetime("2025-12-31T16:00:00")
    assert aa["utc_offset"] == "-08:00"
    pt = aa["specified_points"][0]
    assert pt["fuelbeds"][0]["emissions"]["flaming"]["PM2.5"] == [2.8]
    assert pt["emissions"]["summary"]["PM2.5"] == 4.0
    assert set(aa["timeprofile"]) == {"2025-12-31T16:00:00", "2025-12-31T17:00:00"}


def test_csv_loader_min_qa_filter():
    # fixture: cell 100-200 has QA=3 rows; cell 100-300 has a single QA=2 row.
    # min_qa=3 drops the QA=2 record, leaving only the 100-200 fire.
    loader = rave.CsvFileLoader(
        name="rave", format="CSV", type="file", file=CSV_FIXTURE, min_qa=3,
        group_by="utc")
    assert {f["id"] for f in loader.load()} == {"rave-20260101-100-200"}


## Dispatch (config name/format/type -> loader class)

def test_dispatch_csv_format_resolves_and_loads():
    Config().set([{
        "name": "rave", "format": "CSV", "type": "file", "file": CSV_FIXTURE,
        "group_by": "utc"}],
        "load", "sources")
    fm = FiresManager()
    load_module.run(fm)
    assert fm.num_fires == 2


## Country assignment (default-on via the bundled shapefile)

def _gt_record():
    # Guatemala City (inland) -> resolves to "GT".
    return {"time": "2026-01-01T00:00:00", "lat": 14.6349, "lng": -90.5069,
            "area_km2": 9.0, "pm25_kg": rave.KG_PER_SHORT_TON, "co_kg": 0.0,
            "frp_mw": 10.0, "fre_mj": 0.0, "qa": 3, "row": 1, "col": 2}


def _active_area(loader, records):
    return loader._marshal(records)[0]["activity"][0]["active_areas"][0]


def test_country_assigned_by_default():
    # No country config at all: lookup is on by default via the bundled shapefile.
    loader = rave.NetcdfFileLoader(
        name="rave", format="netcdf", type="file", file="x.nc", group_by="utc")
    aa = _active_area(loader, [_gt_record()])
    assert aa["country"] == "GT"


def test_country_not_assigned_when_disabled():
    loader = rave.NetcdfFileLoader(
        name="rave", format="netcdf", type="file", file="x.nc",
        assign_country=False, group_by="utc")
    aa = _active_area(loader, [_gt_record()])
    assert "country" not in aa


def test_country_shapefile_override():
    loader = rave.NetcdfFileLoader(
        name="rave", format="netcdf", type="file", file="x.nc",
        country_shapefile=DEFAULT_COUNTRIES_SHAPEFILE, group_by="utc")
    aa = _active_area(loader, [_gt_record()])
    assert aa["country"] == "GT"
