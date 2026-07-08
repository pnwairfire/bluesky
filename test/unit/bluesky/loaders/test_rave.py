"""Unit tests for the RAVE loader (bluesky.loaders.rave).

Covers the pure helpers, the record->Fire marshalling, file resolution, the CSV
loader, dispatch, and default-on country assignment. These need no NetCDF sample
data or xarray; the CSV cases use the small fixture in data/rave-input.csv.
(NetCDF-extraction tests that require the multi-MB .nc sample live in the
project's private test area.)
"""

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
    fires = rave._RaveMarshalMixin()._marshal(_records_two_cells())
    assert len(fires) == 2
    ids = sorted(f["id"] for f in fires)
    assert ids == ["rave-20260101-100-200", "rave-20260101-100-300"]
    assert all(f["type"] == "wf" for f in fires)


def test_marshal_cell_a_structure():
    fires = {f["id"]: f for f in rave._RaveMarshalMixin()._marshal(_records_two_cells())}
    a = fires["rave-20260101-100-200"]
    aa = a["activity"][0]["active_areas"][0]
    assert aa["utc_offset"] == "-08:00"
    assert aa["start"] == "2025-12-31T16:00:00"     # local of first UTC hour
    assert aa["end"] == "2026-01-01T16:00:00"       # start + 24h

    pt = aa["specified_points"][0]
    assert pt["lat"] == 40.0 and pt["lng"] == -120.0
    assert round(pt["area"], 3) == 2223.945         # 9 km2 -> acres
    assert pt["frp"] == 150.0                        # mean of 100, 200
    assert pt["consumption"]["summary"]["total"] == [0.0]

    # daily totals in SHORT TONS, split 70/20/10
    em = pt["fuelbeds"][0]["emissions"]
    assert em["flaming"]["PM2.5"] == [2.8] and em["smoldering"]["PM2.5"] == [0.8]
    assert em["residual"]["PM2.5"] == [0.4]
    assert em["flaming"]["CO"] == [5.6]
    assert pt["emissions"]["summary"]["PM2.5"] == 4.0
    assert pt["emissions"]["summary"]["CO"] == 8.0


def test_marshal_timeprofile_local_and_sums_to_one():
    fires = {f["id"]: f for f in rave._RaveMarshalMixin()._marshal(_records_two_cells())}
    tp = fires["rave-20260101-100-200"]["activity"][0]["active_areas"][0]["timeprofile"]
    assert set(tp.keys()) == {"2025-12-31T16:00:00", "2025-12-31T17:00:00"}
    assert tp["2025-12-31T16:00:00"]["flaming"] == 0.25   # 1t / 4t
    assert tp["2025-12-31T17:00:00"]["flaming"] == 0.75   # 3t / 4t
    for entry in tp.values():
        assert set(entry) == {"area_fraction", "flaming", "smoldering", "residual"}
    assert round(sum(e["area_fraction"] for e in tp.values()), 9) == 1.0


def test_marshal_lossless_hourly_reconstruction():
    # Sum_phase timeprofile[h][phase] * emissions[phase][PM2.5] == original hourly tons
    fires = {f["id"]: f for f in rave._RaveMarshalMixin()._marshal(_records_two_cells())}
    aa = fires["rave-20260101-100-200"]["activity"][0]["active_areas"][0]
    em = aa["specified_points"][0]["fuelbeds"][0]["emissions"]
    h16 = aa["timeprofile"]["2025-12-31T16:00:00"]
    reconstructed = sum(h16[p] * em[p]["PM2.5"][0] for p in rave.PHASE_FRACTIONS)
    assert round(reconstructed, 9) == 1.0                 # hour 1 was 1 short ton


def test_marshal_skips_zero_emission_cell():
    recs = [{"time": "2026-01-01T00:00:00", "lat": 1.0, "lng": 1.0, "area_km2": 9.0,
             "pm25_kg": 0.0, "co_kg": 0.0, "frp_mw": 0.0, "fre_mj": 0.0,
             "qa": 3, "row": 1, "col": 1}]
    assert rave._RaveMarshalMixin()._marshal(recs) == []


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
        name="rave", format="CSV", type="file", file=CSV_FIXTURE)
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
        name="rave", format="CSV", type="file", file=CSV_FIXTURE, min_qa=3)
    assert {f["id"] for f in loader.load()} == {"rave-20260101-100-200"}


## Dispatch (config name/format/type -> loader class)

def test_dispatch_csv_format_resolves_and_loads():
    Config().set([{
        "name": "rave", "format": "CSV", "type": "file", "file": CSV_FIXTURE}],
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
        name="rave", format="netcdf", type="file", file="x.nc")
    aa = _active_area(loader, [_gt_record()])
    assert aa["country"] == "GT"


def test_country_not_assigned_when_disabled():
    loader = rave.NetcdfFileLoader(
        name="rave", format="netcdf", type="file", file="x.nc",
        assign_country=False)
    aa = _active_area(loader, [_gt_record()])
    assert "country" not in aa


def test_country_shapefile_override():
    loader = rave.NetcdfFileLoader(
        name="rave", format="netcdf", type="file", file="x.nc",
        country_shapefile=DEFAULT_COUNTRIES_SHAPEFILE)
    aa = _active_area(loader, [_gt_record()])
    assert aa["country"] == "GT"
