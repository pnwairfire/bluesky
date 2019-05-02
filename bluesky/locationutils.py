"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

from geoutils.geojson import get_centroid


INVALID_ACTIVE_AREA_INFO = "Invalid active area data required for determining single, representative lat/lng"
MISSING_LOCATION_INFO_FOR_ACTIVE_AREA = "Missing location information for active area"
MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT = "Missing or invalid lat,lng for specified point"
MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER = "Missing or invalid coodinates for active area perimeter"

class LatLng(object):
    """Determines single lat,lng coordinate best representing given
    active area information
    """

    def __init__(self, active_area):
        if not isinstance(active_area, dict):
            raise ValueError(INVALID_ACTIVE_AREA_INFO)
        self._active_area = active_area
        self._compute()

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    def _compute(self):
        if 'specified_points' in self._active_area:
            try:
                geo_data = {
                    "type": 'MultiPoint',
                    'coordinates': [[float(p['lng']), float(p['lat'])]
                        for p in self._active_area['specified_points']]
                }
            except:
                raise ValueError(MISSING_OR_INVALID_LAT_LNG_FOR_SPECIFIED_POINT)

            coordinate = get_centroid(geo_data)
            self._latitude = coordinate[1]
            self._longitude = coordinate[0]

        elif 'perimeter' in self._active_area:
            try:
                geo_data = {
                    "type": 'Polygon',
                    'coordinates': [
                        self._active_area['perimeter']['polygon']
                    ]
                }
                coordinate = get_centroid(geo_data)
            except:
                raise ValueError(MISSING_OR_INVALID_COORDINATES_FOR_PERIMETER)

            self._latitude = coordinate[1]
            self._longitude = coordinate[0]

        else:
            raise ValueError(MISSING_LOCATION_INFO_FOR_ACTIVE_AREA)
