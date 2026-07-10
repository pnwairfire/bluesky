"""bluesky.countries.lookup

Look up an ISO alpha-2 country code for a lat/lng via point-in-polygon against
a bundled Natural Earth countries shapefile. Modeled on
bluesky.ecoregion.lookup and bluesky.locationutils.Fips (geopandas + shapely).
"""
import os

import geopandas as gpd
from shapely.geometry import Point

from bluesky.exceptions import BlueSkyConfigurationError, BlueSkyGeographyValueError

__all__ = ["CountryLookup", "get_default_lookup", "DEFAULT_COUNTRIES_SHAPEFILE"]

DEFAULT_COUNTRIES_SHAPEFILE = os.path.join(
    os.path.dirname(__file__), "data", "countries.shp")
CODE_FIELD = "ISO_A2"


class CountryLookup:
    """Point-in-polygon country lookup from a bundled countries shapefile."""

    def __init__(self, shapefile=DEFAULT_COUNTRIES_SHAPEFILE):
        self._path = shapefile
        self._gdf = None  # lazy-loaded + cached on first lookup

    def _validate_lat_lng(self, lat, lng):
        if abs(lat) > 90.0 or abs(lng) > 180.0:
            raise BlueSkyGeographyValueError(
                "Invalid lat,lng: {},{}".format(lat, lng))

    def _load(self):
        if self._gdf is None:
            if not os.path.exists(self._path):
                raise BlueSkyConfigurationError(
                    "Countries shapefile not found: {}. It ships with "
                    "bluesky.countries; reinstall bluesky or set "
                    "'country_shapefile'.".format(self._path))
            gdf = gpd.read_file(self._path)
            if gdf.crs is None:
                gdf = gdf.set_crs(epsg=4326)
            elif gdf.crs.to_epsg() != 4326:
                gdf = gdf.to_crs(epsg=4326)
            self._gdf = gdf
        return self._gdf

    def lookup(self, lat, lng):
        """Return the ISO alpha-2 code containing (lat, lng), or None."""
        lat, lng = float(lat), float(lng)
        self._validate_lat_lng(lat, lng)
        gdf = self._load()
        point = Point(lng, lat)  # NOTE: longitude first
        # spatial index narrows to bbox candidates; confirm with exact contains
        for i in gdf.sindex.query(point):
            if gdf.geometry.iloc[i].contains(point):
                code = gdf.iloc[i][CODE_FIELD]
                if code and code != "-99":
                    return code
        return None


_DEFAULT_LOOKUP = None


def get_default_lookup():
    """Process-wide singleton CountryLookup over the bundled shapefile."""
    global _DEFAULT_LOOKUP
    if _DEFAULT_LOOKUP is None:
        _DEFAULT_LOOKUP = CountryLookup()
    return _DEFAULT_LOOKUP
