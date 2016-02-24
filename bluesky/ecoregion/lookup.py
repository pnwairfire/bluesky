"""bluesky.ecoregion.lookup

Note: Code copied from BlueSky Framework and modified significantly.
"""

import os

__author__ = "Joel Dubowy and Sonoma Technology, Inc."
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"


class EcoregionLookup(object):

    # TODO: Handle exceptions here or in calling code ?
    # TODO: always default to western ?

    ECOREGION_SHAPEFILE = os.path.join(os.path.dirname(__file__), 'data', '3ecoregions.shp')
    EXCEPTED_VALUES = ["western","southern","boreal"]

    def lookup(self, lat, lng):
        """Looks up ecoregion from lat/lng

        Note: If a fire's location is defined as a polygon, it's the calling
          code's responsibility to pick a representative lat/lng.
        """

        # A separate algorithm is needed to fill the ecoregion variable.

        ecoregion = self.locate_ecoregion(fireLoc["latitude"], fireLoc["longitude"])

        if ecoregion not in self.EXCEPTED_VALUES:
            # TODO: is this appropriate?
            ecoregion = "western"
        return ecoregion


    #Return the ecoregion for this location (as an int)
    #Returns the string "Unknown" if the time zone could not be determined.
    #Raises an exception if the time zone data file could not be opened.
    def locate_ecoregion(self, latitude, longitude):

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
