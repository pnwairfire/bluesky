
"""bluesky.modules.consumption"""

__author__ = "Joel Dubowy"

class LatLng(object):
    """Determines single lat,lng coordinate best representing given location
    information
    """

    def __init__(self, location):
        if not isinstance(location, dict):
            raise ValueError("Invalid location data required for "
                "determining single lat/lng for fire")
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
        elif 'perimeter' in self._location:
            # TODO: get centroid of perimeter(s); also, can't assume 3-deep nested
            # array (it's 3-deep for MultiPolygon, but not necessarily other shape types)
            # see https://en.wikipedia.org/wiki/Centroid
            self._latitude = self._location['perimeter']['coordinates'][0][0][0][1]
            self._longitude = self._location['perimeter']['coordinates'][0][0][0][0]
        elif 'shape_file' in self._location:
            raise NotImplementedError("Importing of shape data from file not implemented")
        else:
            raise ValueError("Insufficient location data required for "
                "determining single lat/lng for location")
