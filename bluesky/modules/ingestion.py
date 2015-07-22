"""bluesky.modules.ingestion"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

__all__ = [
    'run'
]

def run(fires, config=None):
    """Runs the fire data through consumption calculations, using the consume
    package for the underlying computations.

    Args:
     - fires -- array of fire objects
    Kwargs:
     - config -- optional configparser object
    """
    logging.debug("Running ingestion module")
    fire_ingester = FireIngester(config)
    for fire in fires:
        fire_ingester.ingest(fire)

class FireIngester(object):
    """Inputs, transforms, and validates fire data, recording original copy
    under 'input' key.
    """

    def __init__(self, config=None):
        self._config = config

    SCALAR_FIELDS = {
        "id", "name", "event_id"
    }
    NESTED_FIELDS = {
        "location", "time"
    }

    ##
    ## Public Interface
    ##

    def ingest(self, fire):
        if not fire:
            raise ValueError("Fire contains no data")
        if fire.has_key('input'):
            raise RuntimeError("Fire data was already ingested")

        # move original data under 'input key'
        fire['input'] = { k: fire.pop(k) for k in fire.keys() }

        # copy back down any recognized top level, 'scalar' fields
        for k in self.SCALAR_FIELDS:
            if fire['input'].has_key(k):
                fire[k] = fire['input'][k]

        # Call separate ingest methods for each nested object
        for k in self.NESTED_FIELDS:
            key_ingester = getattr(self, '_ingest_%s' % (k), None)
            key_ingester(fire)

        self._ingest_custom_fields(fire)
        self._set_defaults(fire)
        self._set_derived_fields(fire)
        self._validate(fire)

    ##
    ## General Helper methods
    ##

    def _ingest_custom_fields(self, fire):
        # TODO: copy over custom fields specified in config
        pass

    def _set_defaults(self, fire):
        # TODO: set defaults for any fields that aren't defined; make the
        # defaults configurable, and maybe hard code any
        pass

    def _set_derived_fields(self, fire):
        # TODO: set any other fields (besides 'name') that aren't defined and
        # can and should be set from other fields (like name, id, etc.)
        self._set_derived_name(fire)

    def _set_derived_name(self, fire):
        if fire.get('name'):
            return

        lat = lng = None
        location = fire.get('location')
        if location:
            perimeter = location.get('perimeter')
            if perimeter:
                if perimeter.get('type') == 'MultiPolygon':
                    coords = perimeter.get('coordinates',[])
                    if (0 < len(coords) and 0 < len(coords[0]) and
                            0 < len(coords[0][0]) and 0 < len(coords[0][0][0])):
                        lng = coords[0][0][0][0]
                        lat = coords[0][0][0][1]
                    # else, invalid data; just exlude lat/lng from name
                # TODO: support other perimeter geo data type/formats
            elif location.get('latitude'): # implies lng is defined too
                lat = location['latitude']
                lng = location['longitude']

        fire_id = fire.get("id")
        fire_name = "Fire %s" % (fire_id) if fire_id else "Unnamed fire"

        event_id = fire.get('event_id')
        if event_id:
            fire_name += " from event %s" % (event_id)

        if lat and lng:
            fire_name += " near %.5f, %.5f" % (lat, lng)

        fire['name'] = fire_name

    def _validate(self, fire):
        # TODO: make sure required fields are all defined, and validate
        # values not validated by nested field specific _ingest_* methods
        pass

    def _get_field(self, fire, key, section=None):
        """Looks up field's value in fire object.

        Looks in 'input' > section > key, if section is defined. If not, or if
        key wasn't defined under the section, looks in top level fire object.

        TODO: support synonyms? (ex. what fields are called in fire_locations.csv)
        """
        v = None
        if section:
            v = fire['input'].get(section, {}).get(key)
        if v is None:
            v = fire['input'].get(key)
        return v

    def _get_fields(self, fire, section, optional_fields):
        """Returns dict of specified fields, defined either in top level or
        nested within specified section

        Excludes any fields that are undefined or empty.
        """
        fields = {}
        for k in optional_fields:
            v = self._get_field(fire, k, section)
            if v:
                fields[k] = v
        return fields

    ##
    ## Field-Specific Ingest Methods
    ##

    OPTIONAL_LOCATION_FIELDS = [
        "ecoregion",
        # TODO: fill in others
    ]

    def _ingest_location(self, fire):
        # TODO: validate fields
        # TODO: look for fields either in 'location' key or at top level
        perimeter = self._get_field(fire, 'perimeter', 'location')
        lat = self._get_field(fire, 'latitude', 'location')
        lng = self._get_field(fire, 'longitude', 'location')
        area = self._get_field(fire, 'area', 'location')
        if perimeter:
            fire['location'] = {
                'perimeter': perimeter
            }
        elif lat and lng and area:
            fire['location'] = {
                'latitude': lat,
                'longitude': lng,
                'area': area
            }
        else:
            raise ValueError("Fire object must define perimeter or lat+lng+area")

        fire['location'].update(self._get_fields(fire, 'location',
            self.OPTIONAL_LOCATION_FIELDS))

    OPTIONAL_TIME_FIELDS = [
        "start", "end", "timezone"
    ]

    def _ingest_time(self, fire):
        time_fields = self._get_fields(fire, 'time', self.OPTIONAL_TIME_FIELDS)
        # Only add 'time' key if there are any defined fiespecified fields, defined either in top level or
        if time_fields:
            fire['time'] = time_fields
