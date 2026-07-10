"""Unit tests for looking up country (ISO alpha-2) from lat/lng.

Runs against the bundled bluesky/countries/data/countries.shp (which ships with
the package), so no external data is required.
"""

import geopandas as gpd
from pytest import raises, skip

from bluesky.countries.lookup import (
    CountryLookup, get_default_lookup, DEFAULT_COUNTRIES_SHAPEFILE)
from bluesky.exceptions import (
    BlueSkyGeographyValueError, BlueSkyConfigurationError)


def test_lookup_known_countries():
    cl = CountryLookup()
    assert cl.lookup(19.4326, -99.1332) == "MX"   # Mexico City
    assert cl.lookup(14.6349, -90.5069) == "GT"   # Guatemala City
    assert cl.lookup(39.0, -98.0) == "US"          # Kansas, USA (inland)


def test_lookup_ocean_returns_none():
    assert CountryLookup().lookup(0.0, -140.0) is None   # mid-Pacific


def test_lookup_validates_coords():
    with raises(BlueSkyGeographyValueError):
        CountryLookup().lookup(100.0, 0.0)


def test_lookup_caches_geodataframe():
    cl = CountryLookup()
    assert cl._gdf is None
    cl.lookup(19.4326, -99.1332)
    first = cl._gdf
    assert first is not None
    cl.lookup(14.6349, -90.5069)
    assert cl._gdf is first          # not reloaded on the second call


def test_default_lookup_is_singleton():
    assert get_default_lookup() is get_default_lookup()


def test_missing_shapefile_raises():
    cl = CountryLookup("/nonexistent/countries.shp")
    with raises(BlueSkyConfigurationError):
        cl.lookup(19.4326, -99.1332)


def test_minus99_territory_returns_none():
    # Rows whose ISO_A2 is "-99" (disputed/overseas entities) must resolve to
    # None, not leak "-99" as a country code.
    gdf = gpd.read_file(DEFAULT_COUNTRIES_SHAPEFILE)
    minus99 = gdf[gdf["ISO_A2"] == "-99"]
    if len(minus99) == 0:
        skip("no -99 rows in shapefile")
    pt = minus99.geometry.iloc[0].representative_point()
    assert CountryLookup().lookup(pt.y, pt.x) is None
