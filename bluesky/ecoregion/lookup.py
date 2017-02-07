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

from bluesky.exceptions import BlueSkyGeographyValueError

__author__ = "Joel Dubowy and Sonoma Technology, Inc."
__all__ = ['lookup']


ECOREGION_SHAPEFILE = os.path.join(os.path.dirname(__file__), 'data', '3ecoregions.shp')
# ACCEPTED_VALUES = ["western","southern","boreal"]


## Fiona + shapely

SHAPEFILE_RECORDS = []
with fiona.open(ECOREGION_SHAPEFILE) as shapes:
    SHAPEFILE_RECORDS = [s for s in shapes]

def _validate_lat_lng(lat, lng):
    if abs(lat) > 90.0 or abs(lng) > 180.0:
        raise BlueSkyGeographyValueError(
            "Invalid lat,lng: {},{}".format(lat, lng))

def lookup_ecoregion_shapely(lat, lng):
    """Looks up ecoregion from lat/lng using shapely + fiona

    Note: If a fire's location is defined as a polygon, it's the calling
      code's responsibility to pick a representative lat/lng.
    """
    _validate_lat_lng(lat, lng)

    # TODO: Handle exceptions here or in calling code ?

    # sf = shapefile.Reader(ECOREGION_SHAPEFILE)
    # shapes = sf.shapes()
    point = geometry.Point(lng, lat) # longitude, latitude

    ecoregion = None
    for sr in SHAPEFILE_RECORDS:
        shape = geometry.asShape(sr['geometry'])
        #import pdb;pdb.set_trace()
        if shape.contains(point):
            return sr['properties']['DOMAIN']


## Ogr

DS_IN = ogr.GetDriverByName('ESRI Shapefile').Open(ECOREGION_SHAPEFILE)

def lookup_ecoregion_ogr(lat, lng):
    """Looks up ecoregion from lat/lng using gdal's ogr binding

    Note: If a fire's location is defined as a polygon, it's the calling
      code's responsibility to pick a representative lat/lng.
    """
    _validate_lat_lng(lat, lng)

    lyr_in = DS_IN.GetLayer(0)
    idx_reg = lyr_in.GetLayerDefn().GetFieldIndex("DOMAIN")
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.SetPoint_2D(0, lng, lat)
    lyr_in.SetSpatialFilter(pt)
    for feat_in in lyr_in:
        # roughly subsets features, instead of go over everything
        ply = feat_in.GetGeometryRef()
        if ply.Contains(pt):
            return feat_in.GetFieldAsString(idx_reg)