"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

from geoutils.geojson import get_centroid


INVALID_LOCATION_DATA = ("Invalid location data required for"
    " determining single, representative lat/lng")
MISSING_LOCATION_INFO = ("Missing location information for"
    " determining single, representative lat/lng")

MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT = (
    "Missing or invalid lat,lng for specified point")
MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER = (
    "Missing or invalid coodinates for active area perimeter")

class LatLng(object):
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
                self._compute_from_geo_data('MultiPoint', coordinates)

        elif 'perimeter' in self._location_data:
            self._compute_from_geo_data('Polygon',
                [self._location_data['perimeter'].get('polygon')])

        elif 'polygon' in self._location_data:
            self._compute_from_geo_data('Polygon',
                [self._location_data['polygon']])

        else:
            raise ValueError(MISSING_LOCATION_INFO)

    def _compute_from_geo_data(self, geo_type, coordinates):
        try:
            geo_data = {
                "type": geo_type,
                'coordinates': coordinates
            }
            coordinate = get_centroid(geo_data)
            self._latitude = coordinate[1]
            self._longitude = coordinate[0]

        except:
            error_msg = (MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER
                if geo_type == 'Polygon'
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
