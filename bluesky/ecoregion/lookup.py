"""bluesky.ecoregion.lookup

Note: This code was originally copied from BlueSky Framework, but it has
been modified significantly.
"""

import logging
import os

#import shapefile
import fiona
from shapely import geometry

from bluesky.exceptions import BlueSkyGeographyValueError

__author__ = "Joel Dubowy and Sonoma Technology, Inc."
__all__ = ['lookup']


ECOREGION_SHAPEFILE = os.path.join(os.path.dirname(__file__), 'data', '3ecoregions.shp')
# ACCEPTED_VALUES = ["western","southern","boreal"]

def lookup_ecoregion(lat, lng):
    """Looks up ecoregion from lat/lng

    Note: If a fire's location is defined as a polygon, it's the calling
      code's responsibility to pick a representative lat/lng.
    """
    if abs(lat) > 90.0 or abs(lng) > 180.0:
        raise BlueSkyGeographyValueError(
            "Invalid lat,lng: {},{}".format(lat, lng))

    # TODO: Handle exceptions here or in calling code ?

    # sf = shapefile.Reader(ECOREGION_SHAPEFILE)
    # shapes = sf.shapes()
    point = geometry.Point(lng, lat) # longitude, latitude

    ecoregion = None
    with fiona.open(ECOREGION_SHAPEFILE) as shapes:
        for shapefile_record in shapes:
            shape = geometry.asShape(shapefile_record['geometry'])
            #import pdb;pdb.set_trace()
            if shape.contains(point):
                return shapefile_record['properties']['DOMAIN']
