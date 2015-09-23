"""bluesky.modules.ingestion"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import consume
import logging

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """Ingests the fire data, recording a copy of the raw input and restructuring
    the data as necessary

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object

    Note: The input being recorded may not be purely 'raw', since any fire
      lacking an id will have one auto-generated during Fire object
      instantiation.  Otherwise, what's recorded is the user's input.

    Note: Ingestion typically should only be run once, but the code does *not*
      enforce this.
    """
    logging.debug("Running ingestion module")
    try:
        parsed_input = []
        fire_ingester = FireIngester()
        for fire in fires_manager.fires:
            parsed_input.append(fire_ingester.ingest(fire))
        fires_manager.processed(__name__, __version__, parsed_input=parsed_input)
    except:
        # just record what module was run; the error will be inserted
        # into output data by calling code
        fires_manager.processed(__name__, __version__)
        raise

class FireIngester(object):
    """Inputs, transforms, and validates fire data, recording original copy
    under 'input' key.
    """

    # TODO: support synonyms (?)
    #  ex:
    #    SYNONYMS = {
    #        "date_time": "start"
    #        # TODO: fill in other synonyms
    #    }
    #  with logic like:
    #    for k,v in self.SYNONYMS.items():
    #        if fire.has_key(k) and not fire.has_key(v):
    #            # TDOO: should we pop 'k':
    #            #  >  self[v] = self.pop(k)
    #            fire[v] = fire[k]
    # and do so recursively to get nested objects under fire object

    SCALAR_FIELDS = {
        "id"
    }
    NESTED_FIELDS = {
        "location", "growth", "event_of"
    }

    ##
    ## Public Interface
    ##

    # TODO: refact

    def ingest(self, fire):
        if not fire:
            raise ValueError("Fire contains no data")

        # move original data under 'input key'
        self._parsed_input = { k: fire.pop(k) for k in fire.keys() }

        # copy back down any recognized top level, 'scalar' fields
        for k in self.SCALAR_FIELDS:
            if self._parsed_input.has_key(k):
                fire[k] = self._parsed_input[k]

        # Call separate ingest methods for each nested object
        for k in self.NESTED_FIELDS:
            key_ingester = getattr(self, '_ingest_%s' % (k), None)
            key_ingester(fire)

        self._ingest_custom_fields(fire)
        self._set_defaults(fire)
        self._validate(fire)
        return self._parsed_input

    ##
    ## General Helper methods
    ##

    def _ingest_custom_fields(self, fire):
        # TODO: copy over custom fields specified in config (need to pass
        # ingestion config settings into FireIngester constructor)
        pass

    def _set_defaults(self, fire):
        # TODO: set defaults for any fields that aren't defined; make the
        # defaults configurable, and maybe hard code any
        pass

    def _validate(self, fire):
        # TODO: make sure required fields are all defined, and validate
        # values not validated by nested field specific _ingest_* methods
        pass

    def _get_field(self, key, section=None):
        """Looks up field's value in fire object.

        Looks in 'input' > section > key, if section is defined. If not, or if
        key wasn't defined under the section, looks in top level fire object.

        TODO: support synonyms? (ex. what fields are called in fire_locations.csv)
        """
        v = None
        if section:
            v = self._parsed_input.get(section, {}).get(key)
        if v is None:
            v = self._parsed_input.get(key)
        return v

    def _get_fields(self, section, optional_fields):
        """Returns dict of specified fields, defined either in top level or
        nested within specified section

        Excludes any fields that are undefined or empty.
        """
        fields = {}
        for k in optional_fields:
            v = self._get_field(k, section)
            if v:
                fields[k] = v
        return fields

    ##
    ## Field-Specific Ingest Methods
    ##

    OPTIONAL_LOCATION_FIELDS = [
        "ecoregion",
        # TODO: should timezone be required, or only by modules using met data?
        "timezone"
        # TODO: fill in others
    ]

    def _ingest_location(self, fire):
        # TODO: validate fields
        # TODO: look for fields either in 'location' key or at top level
        perimeter = self._get_field('perimeter', 'location')
        lat = self._get_field('latitude', 'location')
        lng = self._get_field('longitude', 'location')
        area = self._get_field('area', 'location')
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

        fire['location'].update(self._get_fields('location',
            self.OPTIONAL_LOCATION_FIELDS))


    OPTIONAL_EVENT_OF_FIELDS = [
        "name", "id"
    ]

    def _ingest_event_of(self, fire):
        event_of_fields = [
            # 'name' can be defined at the top level as well as under 'event_of'
            ("name", self._get_field("name", 'event_of')),
            # event id, if defined, can be defined as 'event_id' at the top
            # level or as 'id' be under 'event_of'
            ("id", self._parsed_input.get('event_of', {}).get('id') or
                self._parsed_input.get('event_id'))
        ]
        event_of_dict = { k:v for k, v in event_of_fields if v}
        if event_of_dict:
            fire['event_of'] = event_of_dict

    GROWTH_FIELDS = ['start','end', 'pct']

    def _ingest_growth(self, fire):
        # Note: can't use _get_field[s] as is because 'growth' is an array,
        # not a nested object
        growth = []
        if not self._parsed_input.get('growth'):
            # no growth array - look for 'start'/'end' in top level
            start = self._parsed_input.get('start')
            end = self._parsed_input.get('end')
            if start and end:
                growth.append({'start': start, 'end': end, 'pct': 100.0})
        else:
            for g in self._parsed_input['growth']:
                growth.append({})
                for f in self.GROWTH_FIELDS:
                    if not g.get(f):
                        raise ValueError("Missing groth field: '{}'".format(f))
                    growth[-1][f] = g[f]
        if growth:
            # TODO: make sure percentages add up to 100.0, with allowable error
            fire['growth'] = growth
