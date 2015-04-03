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
    fire_ingester = FireIngester()
    for fire in fires:
        ingester.ingest(fire)

class FireIngester(object):

    ##
    ## Public Interface
    ##

    SCALAR_FIELDS = {
        "id", "name", "event_id"
    }
    NESTED_FIELDS = {
        "location", "time"
    }

    def ingest(self, fire):
        if not fire:
            raise ValueError("Fire contains no data")
        if fire.has_key('input'):
            raise RuntimeError("Fire data was already ingested")

        fire['input'] = { k, fire.pop(k) for k in fire.keys() }
        for f in self.SCALAR_FIELDS:
            fire['input'][k] = fire[k]
        for f in self.NESTED_FIELDS:
            key_ingestr = getattr(self, '_ingest_%s' % (k), None)
            key_ingester(fire)

        # TODO: allow other arbitrary fields?

        self._fill_in_fields(fire)
        self._post_process(fire)

    ##
    ## General Helper methods
    ##

    def _fill_in_fields(self, fire):
        # TODO: set defaults for any fields that aren't defined
        # TODO: set any fields that aren't defined and can and
        # should be set from other fields (like name, id, etc.)
        pass

    def _post_process(self, fire):
        # TODO: make sure required fields are all defined
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

        fire['location'].update({
            k:v for k, copy.deepcopy(v) in fire['input']['location'].items()
                if k in self.OPTIONAL_LOCATION_FIELDS
        })

    def _ingest_time(self, fire):
        pass