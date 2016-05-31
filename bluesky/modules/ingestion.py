"""bluesky.modules.ingestion"""

__author__ = "Joel Dubowy"

import copy
import datetime
import logging
import re

from bluesky import consumeutils

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
            with fires_manager.fire_failure_handler(fire):
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

    Currently, for synonyms, you need to create a '_ingest_special_field_*'
    method to rename and record the field in the correct place.

    TODO: add more generic logic to handle simple fields with possible
      synonyms. e.g.

        SYNONYMS = {
            # field, section (optional), synonyms (optional)
            ("foo", None, None),
            ("bar", "location", None),
            ("baz", None, ["baaz", "baaaaz"])
        }

        for field, section, synonyms in SYNONYMS:
            v = None
            for f in [field] + (synonyms or []):
                v = self._get_field(f, section)
                if v:
                    break
            if v:
                if section:
                    if 'section' not in fire:
                        fire['section'] = {}
                    fire['section'][field] = v
                else:
                    fire[field] = v

      and, if necessary, refactor to support arbitrary section nesting
    """

    SCALAR_FIELDS = {
        "id", "type", "fuel_type"
    }
    # TODO: do anything with other fields found in daily SF2 data
    #     > 'owner','sf_event_guid','sf_server','sf_stream_name','fips','scc'

    NESTED_FIELD_METHOD_PREFIX = '_ingest_nested_field_'
    SPECIAL_FIELD_METHOD_PREFIX = '_ingest_special_field_'

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
        for k in dir(self):
            if k.startswith(self.NESTED_FIELD_METHOD_PREFIX):
                getattr(self, k)(fire)

        # Ingest special fields; it's important that this happens after
        # the above ingest method calls
        for k in dir(self):
            if k.startswith(self.SPECIAL_FIELD_METHOD_PREFIX):
                getattr(self, k)(fire)

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
            if v is not None:
                fields[k] = v
        return fields

    ##
    ## Nested Field Specific Ingest Methods
    ##

    ## 'location'

    OPTIONAL_LOCATION_FIELDS = [
        "ecoregion",
        # utc_offset is for the most part required by modules using met data
        # (but not exclusively; e.g. FEPS plumerise uses it)
        "utc_offset",
        # SF2 weather, moisture, etc. fields
        'elevation','slope',
        'state','county','country',
        'fuel_1hr','fuel_10hr','fuel_100hr',
        'fuel_1khr','fuel_10khr','fuel_gt10khr',
        'canopy','shrub','grass','rot','duff', 'litter',
        'moisture_1hr','moisture_10hr',
        'moisture_100hr','moisture_1khr',
        'moisture_live','moisture_duff',
        'min_wind','max_wind',
        'min_wind_aloft', 'max_wind_aloft',
        'min_humid','max_humid',
        'min_temp','max_temp',
        'min_temp_hour','max_temp_hour',
        'sunrise_hour','sunset_hour',
        'snow_month','rain_days'
        # TODO: fill in others
    ]
    for a in consumeutils.SETTINGS.values():
        for b in a:
            OPTIONAL_LOCATION_FIELDS.append(b['field'])
            if 'synonyms' in b:
                OPTIONAL_LOCATION_FIELDS.extend(b['synonyms'])
    # remove dupes
    OPTIONAL_LOCATION_FIELDS = list(set(OPTIONAL_LOCATION_FIELDS))

    def _ingest_nested_field_location(self, fire):
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

    ## 'event_of'

    def _ingest_nested_field_event_of(self, fire):
        event_of_fields = [
            # 'name' can be defined at the top level as well as under 'event_of'
            ("name", self._get_field("name", 'event_of')),
            # event id, if defined, can be defined as 'event_id' at the top
            # level or as 'id' under 'event_of'
            ("id", self._parsed_input.get('event_of', {}).get('id') or
                self._parsed_input.get('event_id')),
            # event url, if defined, can be defined as 'event_url' at the top
            # level or as 'url' under 'event_of'
            ("url", self._parsed_input.get('event_of', {}).get('url') or
                self._parsed_input.get('event_url'))
        ]
        event_of_dict = { k:v for k, v in event_of_fields if v}

        if event_of_dict:
            fire['event_of'] = event_of_dict

    ## 'growth'

    GROWTH_FIELDS = ['start','end', 'pct']
    OPTIONAL_GROWTH_FIELDS = ['localmet', 'timeprofile', 'plumerise']

    def _ingest_optional_growth_fields(self, growth, src):
        for f in self.OPTIONAL_GROWTH_FIELDS:
            v = src.get(f)
            if v:
                growth[-1][f] = v

    def _ingest_nested_field_growth(self, fire):
        # Note: can't use _get_field[s] as is because 'growth' is an array,
        # not a nested object
        growth = []
        if not self._parsed_input.get('growth'):
            # no growth array - look for 'start'/'end' in top level
            start = self._parsed_input.get('start')
            end = self._parsed_input.get('end')
            if start and end:
                growth.append({'start': start, 'end': end, 'pct': 100.0})
                self._ingest_optional_growth_fields(growth, self._parsed_input)

        else:
            for g in self._parsed_input['growth']:
                growth.append({})
                for f in self.GROWTH_FIELDS:
                    if not g.get(f):
                        raise ValueError("Missing groth field: '{}'".format(f))
                    growth[-1][f] = g[f]
                self._ingest_optional_growth_fields(growth, g)

        if growth:
            if len(growth) == 1 and 'pct' not in growth[0]:
                growth[0] = 100.0
            # TODO: make sure percentages add up to 100.0, with allowable error
            fire['growth'] = growth

    ## 'fuelbeds'

    OPTIONAL_FUELBED_FIELDS = [
        'fccs_id', 'pct', 'fuel_loadings',
        'consumption', 'emissions', 'emissions_details'
    ]
    # TODO: do anything with fuelbed related data found in daily SF2 data ?
    #   e.g.:
    #     > consumption_flaming,consumption_smoldering,consumption_residual,
    #     > consumption_duff, heat,pm25,pm10,co,co2,ch4,nox,nh3,so2,voc,
    #     > fccs_number,veg

    def _ingest_nested_field_fuelbeds(self, fire):
        if self._parsed_input.get('fuelbeds'):
            fuelbeds = []
            for fb in self._parsed_input['fuelbeds']:
                fuelbed = {}
                for f in self.OPTIONAL_FUELBED_FIELDS:
                    v = fb.get(f)
                    if v:
                        fuelbed[f] = v
                if fuelbed:
                    fuelbeds.append(fuelbed)

            if fuelbeds:
                fire['fuelbeds'] = fuelbeds

    ## 'meta'

    def _ingest_nested_field_meta(self, fire):
        # just copy all of 'meta', if it's defined
        if self._parsed_input.get('meta'):
            fire['meta'] = copy.deepcopy(self._parsed_input['meta'])

    ##
    ## Special Field Ingest Methods
    ##

    # TODO: grab 'timezone' and store in 'location' > 'timezone' (if not already
    #   defined); note that it's not the same as utc_offset - utc_offset reflects
    #   daylight savings and thus is the true offset from UTC, whereas timezone
    #   does not change; e.g. an agust 5th fire in Florida is listed with timezone
    #   -5.0 and utc_offset (embedded in the 'date_time' field) '-04:00'

    ## 'date_time'
    OLD_DATE_TIME_MATCHER = re.compile('^(\d{12})(\d{2})?Z$')
    DATE_TIME_MATCHER = re.compile('^(\d{12})(\d{2})?([+-]\d{2}\:\d{2})$')
    DATE_TIME_FMT = "%Y%m%d%H%M"
    GROWTH_TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
    def _ingest_special_field_date_time(self, fire):
        """Ingests/parses 'date_time' field, found in sf2 fire data

        Note: older SF2 fire data formatted the date_time field without
        local timezone information, mis-representing everything as
        UTC.  E.g.:

            '201405290000Z'

        Newer (and current) SF2 fire data formats date_time like so:

            '201508040000-04:00'

        With true utc offset embedded in the string.
        """
        if not fire['location'].get('utc_offset') or not fire.get('growth'):
            date_time = self._parsed_input.get('date_time')
            if date_time:
                # this supports fires from bluesky daily runs;
                # 'date_time' is formatted like: '201508040000-04:00'
                try:
                    start = None
                    utc_offset = None
                    m = self.DATE_TIME_MATCHER.match(date_time)
                    if m:
                        start = datetime.datetime.strptime(
                            m.group(1), self.DATE_TIME_FMT)
                        utc_offset = m.group(3)
                    else:
                        m = self.OLD_DATE_TIME_MATCHER.match(date_time)
                        if m:
                            start = datetime.datetime.strptime(
                                m.group(1), self.DATE_TIME_FMT)
                            # Note: we don't know utc offset; don't set

                    if start is not None and not fire.get('growth'):
                        # As assume 24-hour
                        end = start + datetime.timedelta(hours=24)
                        # Note: this assumes time is local
                        fire['growth'] =[{
                            'start': start.strftime(self.GROWTH_TIME_FORMAT),
                            'end': end.strftime(self.GROWTH_TIME_FORMAT),
                            'pct': 100.0
                        }]

                    if utc_offset is not None and not fire['location'].get(
                            'utc_offset'):
                        fire['location']['utc_offset'] = utc_offset

                except Exception, e:
                    logging.warn("Failed to parse 'date_time' value %s",
                        date_time)
