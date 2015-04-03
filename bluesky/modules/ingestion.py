"""bluesky.modules.ingestion"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

__all__ = [
    'run'
]

def run(fires, options=None):
    """Runs the fire data through consumption calculations, using the consume
    package for the underlying computations.

    Args:
     - fires -- array of fire objects
    Kwargs:
     - config -- optional configparser object
    """
    logging.debug("Running ingestion module")
    fire_ingester = FireIngester(options)
    for fire in fires:
        ingester.ingest(fire)

class FireIngester(object):
    """Inputs, transforms, and validates fire data, recording original copy
    under 'input' key.
    """

    def __init__(self, options=None):
        self._options = options

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
        for f in self.SCALAR_FIELDS:
            if fire['input'].has_key(k):
                fire[k] = fire['input'][k]

        # Call separate ingest methods for each nested object
        for f in self.NESTED_FIELDS:
            key_ingestr = getattr(self, '_ingest_%s' % (k), None)
            key_ingester(fire)

        self._ingest_custom_fields(fire)
        self._fill_in_fields(fire)
        self._validate(fire)

    ##
    ## General Helper methods
    ##

    def _ingest_custom_fields(self, fire):
        # TODO: copy over custom fields specified in options
        pass

    def _fill_in_fields(self, fire):
        # TODO: set defaults for any fields that aren't defined
        # TODO: set any fields that aren't defined and can and
        # should be set from other fields (like name, id, etc.)
        pass

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
        lng = self._get_field(fire, 'latitude', 'longitude')
        area = self._get_field(fire, 'latitude', 'area')
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

        fire['location'].update(self._get_fields(fire, section, 'location'))

    OPTIONAL_TIME_FIELDS = [
        "start", "end", "timezone"
    ]

    def _ingest_time(self, fire):
        time_fields = self._get_fields(fire, section, 'time')
        # Only add 'time' key if there are any defined fiespecified fields, defined either in top level or
        if time_fields:
            fire['time'] = time_fields
