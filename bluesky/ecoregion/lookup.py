"""bluesky.ecoregion.lookup

Note: This code was originally copied from BlueSky Framework, but it has
been modified significantly.
"""

import logging
import os

try:
    import mapscript
    from osgeo import ogr
except ImportError as e:
    from bluesky import exceptions
    raise exceptions.MissingDependencyError(
        "Missing dependencies required for ecoregion lookup - {}".format(e))

__author__ = "Joel Dubowy and Sonoma Technology, Inc."
__all__ = ['lookup']


ECOREGION_SHAPEFILE = os.path.join(os.path.dirname(__file__), 'data', '3ecoregions.shp')
ACCEPTED_VALUES = ["western","southern","boreal"]

@classmethod
def lookup_ecoregion(lat, lng):
    """Looks up ecoregion from lat/lng

    Note: If a fire's location is defined as a polygon, it's the calling
      code's responsibility to pick a representative lat/lng.
    """
    # TODO: Handle exceptions here or in calling code ?

    ecoregion = _locate_ecoregion(lat, lng)
    if ecoregion not in ACCEPTED_VALUES:
        # TODO: is this appropriate?
        ecoregion = "western"
    return ecoregion


@classmethod
def _locate_ecoregion(latitude, longitude):
    """Returns the ecoregion for given location (as an int)

    Returns the string "Unknown" if the time zone could not be determined.
    Raises an exception if the time zone data file could not be opened.
    """
    # Instantiate mapscript shapefileObj
    # will later be used to read features in the shapefile
    shpfile = mapscript.shapefileObj(ECOREGION_SHAPEFILE, -1)     # -1 indicates file already exists
    numShapes = shpfile.numshapes                    # stores the number of shapes from the shapefileObj

    # store fire location longitude, latitude in mapscript pointOb
    # used to determine if pointObj is within global region features
    point = mapscript.pointObj(longitude, latitude)

    # determine if feature in shpfile contains fire location point
    ecoregion_number = 0
    while (ecoregion_number < numShapes):
        shape = shpfile.getShape(ecoregion_number)
        if shape.contains(point):
            break
        else:
            ecoregion_number += 1

    # get the shapefile driver
    driver = ogr.GetDriverByName('ESRI Shapefile')

    # open the data source
    datasource = ogr.Open(ECOREGION_SHAPEFILE)
    if datasource is None:
        logging.info("Could not open time zone shapefile")

    # get the data layer
    layer = datasource.GetLayerByIndex(0)
    layer.ResetReading()

    feature = layer.GetFeature(ecoregion_number)

    # test if the lat/lon was found inside one of the ecoregions
    if feature is None:
        val = 0
    else:
        val = feature.GetFieldAsString('DOMAIN')

    # close the data source
    datasource.Destroy()

    # if the value is empty, assign it to zero
    if val in ("", None):
        val = 0

    return val
