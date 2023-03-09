"""bluesky.ecoregion.lookup

Note: This code was originally copied from BlueSky Framework, but it has
been modified significantly.
"""

import logging
import os

#import shapefile
import fiona
import ogr
from shapely import geometry

from bluesky.exceptions import (
    BlueSkyGeographyValueError,
    BlueSkyConfigurationError
)

__author__ = "Joel Dubowy and Sonoma Technology, Inc."
__all__ = ['lookup']


ECOREGION_SHAPEFILE = os.path.join(os.path.dirname(__file__), 'data', '3ecoregions.shp')
# ACCEPTED_VALUES = ["western","southern","boreal"]


class EcoregionLookup():

    def __init__(self, implementation='ogr'):
        try:
            self._lookup = getattr(self, '_lookup_ecoregion_{}'.format(
                implementation))
        except AttributeError:
            raise BlueSkyConfigurationError(
                "Invalid ecoregion lookup implementation: %s", implementation)

        self._input = None # instantiate when necessary

    def _validate_lat_lng(self, lat, lng):
        if abs(lat) > 90.0 or abs(lng) > 180.0:
            raise BlueSkyGeographyValueError(
                "Invalid lat,lng: {},{}".format(lat, lng))

    def lookup(self, lat, lng):
        logging.debug("Looking up ecoregion for %s, %s", lat, lng)
        self._validate_lat_lng(lat, lng)

        # TODO: Handle exceptions here or in calling code ?
        return self._lookup(lat, lng)

    ## Fiona + shapely

    def _lookup_ecoregion_shapely(self, lat, lng):
        """Looks up ecoregion from lat/lng using shapely + fiona

        Note: If a fire's location is defined as a polygon, it's the calling
          code's responsibility to pick a representative lat/lng.
        """
        self._validate_lat_lng(lat, lng)

        if not self._input:
            with fiona.open(ECOREGION_SHAPEFILE) as shapes:
                # need to crate new list out of shapes collection, since
                # `shapes` becomse invalid once out of this context
                self._input = [s for s in shapes]

        # sf = shapefile.Reader(ECOREGION_SHAPEFILE)
        # shapes = sf.shapes()
        point = geometry.Point(lng, lat) # longitude, latitude

        ecoregion = None
        for sr in self._input:
            polygon = geometry.asShape(sr['geometry'])
            if polygon.contains(point):
                return sr['properties']['DOMAIN']

    ## Ogr

    def _lookup_ecoregion_ogr(self, lat, lng):
        """Looks up ecoregion from lat/lng using gdal's ogr binding

        Note: If a fire's location is defined as a polygon, it's the calling
          code's responsibility to pick a representative lat/lng.
        """
        self._validate_lat_lng(lat, lng)

        if not self._input:
            self._input = ogr.GetDriverByName('ESRI Shapefile').Open(
                ECOREGION_SHAPEFILE)

        layer = self._input.GetLayer(0)
        field_index = layer.GetLayerDefn().GetFieldIndex("DOMAIN")
        point = ogr.Geometry(ogr.wkbPoint)
        point.SetPoint_2D(0, lng, lat)
        layer.SetSpatialFilter(point)
        for shape in layer:
            polygon = shape.GetGeometryRef()
            if polygon.Contains(point):
                return shape.GetFieldAsString(field_index)
