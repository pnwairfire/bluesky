"""bluesky.ecoregion.lookup

Note: Code copied from BlueSky Framework and modified significantly.

TODO: refactor code to not be in a class, or use classmethods ?
"""

import os

try:
    import mapscript
    from osgeo import ogr
except ImportError, e:
    from bluesky import exceptions
    raise exceptions.MissingDependencyError(
        "Missing dependencies required for ecoregion lookup - {}".format(e))

__author__ = "Joel Dubowy and Sonoma Technology, Inc."
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"


class EcoregionLookup(object):

    ECOREGION_SHAPEFILE = os.path.join(os.path.dirname(__file__), 'data', '3ecoregions.shp')
    ACCEPTED_VALUES = ["western","southern","boreal"]

    def lookup(self, lat, lng):
        """Looks up ecoregion from lat/lng

        Note: If a fire's location is defined as a polygon, it's the calling
          code's responsibility to pick a representative lat/lng.
        """
        # TODO: Handle exceptions here or in calling code ?

        ecoregion = self._locate_ecoregion(lat, lng)
        if ecoregion not in self.ACCEPTED_VALUES:
            # TODO: is this appropriate?
            ecoregion = "western"
        return ecoregion


    def _locate_ecoregion(self, latitude, longitude):
        """Returns the ecoregion for given location (as an int)

        Returns the string "Unknown" if the time zone could not be determined.
        Raises an exception if the time zone data file could not be opened.
        """
        # Instantiate mapscript shapefileObj
        # will later be used to read features in the shapefile
        shpfile = mapscript.shapefileObj(self.ECOREGION_SHAPEFILE, -1)     # -1 indicates file already exists
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
        datasource = ogr.Open(self.ECOREGION_SHAPEFILE)
        if datasource is None:
            self.log.info("Could not open time zone shapefile")

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
