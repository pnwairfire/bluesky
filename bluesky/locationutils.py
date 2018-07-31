"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

from geoutils.geojson import get_centroid

class LatLng(object):
    """Determines single lat,lng coordinate best representing given location
    information
    """

    def __init__(self, location):
        if not isinstance(location, dict):
            raise ValueError("Invalid location data required for "
                "determining single lat/lng for growth window")
        self._location = location
        self._compute()

    @property
    def latitude(self):
        return self._latitude

    @property
    def longitude(self):
        return self._longitude

    def _compute(self):
        if 'latitude' in self._location and 'longitude' in self._location:
            self._latitude = self._location['latitude']
            self._longitude = self._location['longitude']
        elif 'geojson' in self._location:
            coordinate = get_centroid(self._location['geojson'])
            self._latitude = coordinate[1]
            self._longitude = coordinate[0]
        elif 'shape_file' in self._location:
            raise NotImplementedError("Importing of shape data from file not implemented")
        else:
            raise ValueError("Insufficient location data required for "
                "determining single lat/lng for location")
