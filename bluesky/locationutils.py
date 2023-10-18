"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

# FIPS
import os
import logging
import json
import requests
import zipfile

import geopandas as gpd
import fiona
from shapely.geometry import Point
from geoutils.geojson import get_centroid

INVALID_LOCATION_DATA = ("Invalid location data required for"
    " determining single, representative lat/lng")
MISSING_LOCATION_INFO = ("Missing location information for"
    " determining single, representative lat/lng")

MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT = (
    "Missing or invalid lat,lng for specified point")
MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER = (
    "Missing or invalid coodinates for active area perimeter")

INVALID_LAT_LNG_DATA = ("Invalid latitude or longitude were entered. Ensure they are float"
    " values")
INVALID_FIPS_RESPONSE = ("An Error Occurred Locating the FIPS code for this Lat/Lng")

class LatLng():
    """Determines single lat,lng coordinate best representing given
    active area information
    """

    def __init__(self, location_data):
        if not isinstance(location_data, dict):
            raise ValueError(INVALID_LOCATION_DATA)
        self._location_data = location_data
        self._compute()

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    def _compute(self):
        if set(['lat', 'lng']).issubset(self._location_data):
            self._set_from_specified_point(self._location_data)

        elif 'specified_points' in self._location_data:
            if len(self._location_data['specified_points']) == 1:
                self._set_from_specified_point(
                    self._location_data['specified_points'][0])

            else:
                try:
                    coordinates = [[float(p['lng']), float(p['lat'])]
                        for p in self._location_data['specified_points']]
                except:
                    raise ValueError(MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT)
                self._compute_from_geo_data({
                    "type": 'MultiPoint',
                    'coordinates': coordinates
                })

        elif ('perimeter' in self._location_data
                and self._location_data['perimeter'].get('geometry')):
            self._compute_from_geo_data(
                self._location_data['perimeter']['geometry'])

        elif 'geometry' in self._location_data:
            self._compute_from_geo_data(
                self._location_data.get('geometry'))

        elif 'polygon' in self._location_data:
            logging.warning("Location data should define a "
                "perimeter with 'geometry', not 'polygon'")
            self._compute_from_geo_data({
                'type': 'Polygon',
                'coordinate': self._location_data['polygon']
            })

        else:
            raise ValueError(MISSING_LOCATION_INFO)

    def _compute_from_geo_data(self, geo_data):
        try:
            coordinate = get_centroid(geo_data)
            self._latitude = coordinate[1]
            self._longitude = coordinate[0]

        except:
            error_msg = (MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER
                if geo_data["type"] in ('Polygon', 'MultiPolygon')
                else MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT)
            raise ValueError(error_msg)

    def _set_from_specified_point(self, specified_point):
        """Sets lat and lng from specified point, casting values to float
        """
        try:
            self._latitude = float(specified_point['lat'])
            self._longitude = float(specified_point['lng'])
        except:
            raise ValueError(MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT)

class Fips():
    """
    Returns FIPS metadata from a given Lat/Lng

    Defautls to trying the FCC Census API:
    https://geo.fcc.gov/api/census/#!/block/get_block_find

    Falls back to using the counties_shp file, which is a more
    memory intensive operation.
    """

    def __init__(self, lat, lng):
        if type(lat) is not float or type(lng) is not float:
            try:
                lat = float(lat)
                lng = float(lng)
            except:
                raise ValueError(INVALID_LAT_LNG_DATA)

        self.lat = float(lat)
        self.lng = float(lng)
        self._get_fips()

    @property
    def county_name(self):
        return self._county_name

    @property
    def county_fips(self):
        return self._county_fips

    @property
    def state_name(self):
        return self._state_name

    @property
    def state_fips(self):
        return self._state_fips

    @property
    def state_code(self):
        return self._state_code

    def _get_fips(self):
        # try API and fallback to Shapefile
        url = "https://geo.fcc.gov/api/census/block/find?latitude={}&longitude={}&format=json".format(self.lat, self.lng)

        try:
            r = requests.get(url)
            if r.status_code == 200:
                data = json.loads(r.content.decode())
                self._process_api_data(data)
            else:
                self._get_shp_data()
        except:
            self._get_shp_data()

    def _process_api_data(self, data):
        # process the response payload from the API
        self._county_name = data['County']['name']
        self._county_fips = data['County']['FIPS']
        self._state_name = data['State']['name']
        self._state_fips = data['State']['FIPS']
        self._state_code = data['State']['code']

    def _get_shp_data(self):
        # get counties_fips shapefile
        filename = os.path.join(os.path.dirname(__file__), 'fips', 'counties_fips.shp')

        # load into geopandas and set CRS
        gdf = gpd.read_file(filename)
        gdf = gdf.to_crs(epsg=4326)

        # Shapely point
        p = Point(self.lng, self.lat)

        # apply lambda to determine if point is within the geometry of the object
        gdf['match'] = gdf.geometry.apply(lambda x: p.within(x))

        # return matches
        resdf = gdf.loc[gdf.match == True]

        # only one row should be retuned
        if len(resdf.index) == 1:
            self._process_shp_data(resdf.iloc[0])
        else:
            raise RuntimeError(INVALID_FIPS_RESPONSE)

    def _process_shp_data(self, data):
        # process the response payload from the SHP file
        self._county_name = data.NAME
        self._county_fips = data.GEOID
        self._state_name = None
        self._state_fips = data.STATEFP
        self._state_code = None

def load_perimeter_geometry_from_shapefile(shapefile_name):
    shapefile_name = os.path.abspath(shapefile_name)

    # If a zipfile, extract and set shapefile_name to .shp file
    if shapefile_name.endswith('.zip'):
        with zipfile.ZipFile(shapefile_name, 'r') as zip_ref:
            zip_dir = shapefile_name.replace('.zip', '')
            zip_ref.extractall(zip_dir)
            for f in os.listdir(zip_dir):
                if f.endswith('.shp'):
                    shapefile_name = os.path.join(zip_dir, f)

    with fiona.open(shapefile_name) as features:
        # TODO: support multiple features
        if len(features) > 1:
            raise ValueError("Only shapesfiles with single feature are supported")

        if features[0]['geometry']['type'] not in ('Polygon', 'MultiPolygon'):
            raise ValueError("Perimeter shapefile must be of type Polygon or MultiPolygon")

        return {
            "type": features[0]['geometry'].type,
            "coordinates": features[0]['geometry'].coordinates
        }
