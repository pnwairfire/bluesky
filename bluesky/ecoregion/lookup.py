"""bluesky.ecoregion.lookup

Note: This code was originally copied from BlueSky Framework, but it has
been modified significantly.
"""

import logging
import os

#import shapefile
import fiona
from osgeo import ogr
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

    def __init__(self, implementation='ogr', try_nearby=False):
        try:
            self._lookup = getattr(self, '_lookup_ecoregion_{}'.format(
                implementation))

        except AttributeError:
            raise BlueSkyConfigurationError(
                "Invalid ecoregion lookup implementation: %s", implementation)
        self._try_nearby = try_nearby
        self._input = None # instantiate when necessary

    def _validate_lat_lng(self, lat, lng):
        if abs(lat) > 90.0 or abs(lng) > 180.0:
            raise BlueSkyGeographyValueError(
                "Invalid lat,lng: {},{}".format(lat, lng))

    def lookup(self, lat, lng):
        logging.debug("Looking up ecoregion for %s, %s", lat, lng)
        self._validate_lat_lng(lat, lng)

        # TODO: Handle exceptions here or in calling code ?
        ecoregion = None
        exc = None
        try:
            ecoregion = self._lookup(lat, lng)
        except Exception as e:
            exc = e

        if not ecoregion and self._try_nearby:
            ecoregion = self._lookup_nearby(lat, lng)

        if not ecoregion and exc:
            # raise original exeption if nearby locations all failed
            raise exc

        return ecoregion

    def _lookup_nearby(self, lat, lng):
        delta = 0.01
        locs = [
            (lat + delta, lng),         # N
            (lat + delta, lng + delta), # NE
            (lat, lng + delta),         # E
            (lat - delta, lng + delta), # SE
            (lat - delta, lng),         # S
            (lat - delta, lng - delta), # SW
            (lat, lng - delta),         # W
            (lat + delta, lng - delta), # NW
        ]
        logging.debug("Looking up ecoregion nearby %s, %s - %s", lat, lng, locs)
        for _lat, _lng in locs:
            try:
                return self._lookup(_lat, _lng)
            except:
                # continue on to next nearby location
                pass

        # no nearby locations worked; return None


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
            polygon = geometry.shape(sr['geometry'])
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
