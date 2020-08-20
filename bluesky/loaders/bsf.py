"""bluesky.loaders.bsf

BSF csv structure

id,event_id,latitude,longitude,type,area,date_time,slope,state,county,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,consumption_flaming,consumption_smoldering,consumption_residual,consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm25,pm10,co,co2,ch4,nox,nh3,so2,voc,VEG,canopy,event_url,fccs_number,owner,sf_event_guid,sf_server,sf_stream_name,timezone
SF11C77574457421602580,SF11E4146026,27.188,-81.113,RX,67.999999831,201905280000-04:00,10.0,FL,,USA,12043,2810015000,0.5,0.25,0.25,0.0,0.0,0.0,2.2,0.0,1.0,0.0,1.0,10.0,12.0,12.0,22.0,130.0,150.0,4.48236738577,0.430136575756,0.332945533864,0.0,6.0,6.0,6.0,6.0,40.0,80.0,13.0,30.0,4,14,6,19,5,8,710946484.545042,3.0819790000000005,3.6367379999999994,32.78775999999999,575.1165699999999,1.676383,0.784719,0.5446900000000001,0.349551,7.829838999999999,Default Unknown Fuel Type,0.0,http://128.208.123.111/smartfire/events/f037f5b4-01c3-4223-bee4-8dfc0e7b9967,0,,f037f5b4-01c3-4223-bee4-8dfc0e7b9967,128.208.123.111,realtime,-5.0

"""

__author__ = "Joel Dubowy"

import copy
import datetime
import logging
import re
import traceback
import uuid
from collections import defaultdict

from pyairfire.io import CSV2JSON

from bluesky.models.fires import Fire
from . import BaseCsvFileLoader, skip_failures
from bluesky.datetimeutils import parse_datetime, parse_utc_offset

__all__ = [
    'CsvFileLoader'
]


##
## Loader Classes
##

ONE_DAY = datetime.timedelta(days=1)

def get_optional_float(val):
    # CSV2JSON should have already converted floats, but this is just
    # in case it didn't
    if val not in ('', None):
        return float(val)
    # else return None

LOCATION_FIELDS = [
    # structure:  (csv_key, location_attr, conversion_func)
    # string fields
    ("state", "state", lambda val: val),
    ("county", "county", lambda val: val),
    ("country", "country", lambda val: val),
    # required float fields
    ("latitude", "lat", lambda val: float(val)),
    ("longitude", "lng", lambda val: float(val)),
    # optional float fields
    ("area", "area", get_optional_float),
    ("slope", "slope", get_optional_float),
    ("fuel_1hr", "fuel_1hr", get_optional_float),
    ("fuel_10hr", "fuel_10hr", get_optional_float),
    ("fuel_100hr", "fuel_100hr", get_optional_float),
    ("fuel_1khr", "fuel_1khr", get_optional_float),
    ("fuel_10khr", "fuel_10khr", get_optional_float),
    ("fuel_gt10khr", "fuel_gt10khr", get_optional_float),
    ("moisture_1hr", "moisture_1hr", get_optional_float),
    ("moisture_10hr", "moisture_10hr", get_optional_float),
    ("moisture_100hr", "moisture_100hr", get_optional_float),
    ("moisture_1khr", "moisture_1khr", get_optional_float),
    ("moisture_live", "moisture_live", get_optional_float),
    ("moisture_duff", "moisture_duff", get_optional_float),
    ("min_wind", "min_wind", get_optional_float),
    ("max_wind", "max_wind", get_optional_float),
    ("min_wind_aloft", "min_wind_aloft", get_optional_float),
    ("max_wind_aloft", "max_wind_aloft", get_optional_float),
    ("min_humid", "min_humid", get_optional_float),
    ("max_humid", "max_humid", get_optional_float),
    ("min_temp", "min_temp", get_optional_float),
    ("max_temp", "max_temp", get_optional_float),
    ("min_temp_hour", "min_temp_hour", get_optional_float),
    ("max_temp_hour", "max_temp_hour", get_optional_float),
    ("sunrise_hour", "sunrise_hour", get_optional_float),
    ("sunset_hour", "sunset_hour", get_optional_float),
    ("snow_month", "snow_month", get_optional_float),
    ("rain_days", "rain_days", get_optional_float)
]
# ignored fields: fips, scc, fuel_1hr, fuel_10hr, fuel_100hr, fuel_1khr,
#   fuel_10khr, fuel_gt10khr, shrub, grass, rot, duff, litter,
#   heat, pm25, pm10, co, co2, ch4, nox, nh3, so2, voc, VEG,
#   canopy, fccs_number, owner, sf_event_guid, sf_server,
#   sf_stream_name, timezone
#
#   consumption_flaming, consumption_smoldering,
#   consumption_residual, consumption_duff
#   are handled below

class CsvFileLoader(BaseCsvFileLoader):

    def __init__(self, **config):
        super().__init__(**config)
        self._omit_nulls = config.get('omit_nulls')
        self._timeprofile_file = config.get('timeprofile_file')
        self._load_consumption = config.get('load_consumption')


    def _marshal(self, data):
        self._load_timeprofile_file()

        fires = {}
        self._consumption_values = {}

        for row in data:
            with skip_failures(self._skip_failures):
                fire = self._process_row(row)
                if fire["id"] not in fires:
                    fires[fire["id"]] = fire
                else:
                    # wait to the end to set so that, failure and if
                    # skip_failures == true, the fires[fire["id"]] will be
                    # left as it is
                    fires[fire["id"]] = self._merge(fires[fire["id"]], fire)

        processed_fires = []
        for fire in fires.values():
            with skip_failures(self._skip_failures):
                self._post_process_activity(fire)
                processed_fires.append(fire)

        return processed_fires

    def _merge(self, fire1, fire2):
        merged_fire = copy.deepcopy(fire1)
        merged_fire['specified_points_by_date_n_offset'].update(
            fire2['specified_points_by_date_n_offset'])
        merged_fire['event_of'].update(fire2['event_of'])
        if 'type' in fire2:
            # TODO: if defined, make sure fire1's type doesn't differ
            merged_fire['type'] = fire2['type']

        return merged_fire

    def _load_timeprofile_file(self):
        self._timeprofile = defaultdict(lambda: defaultdict(lambda: {}))
        if self._timeprofile_file:
            csv_loader = CSV2JSON(input_file=self._timeprofile_file)
            data = csv_loader._load()
            for row in data:
                event_id = row['Fire']
                day = datetime.datetime.strptime(row['LocalDay'], '%Y-%m-%d')
                # ts needs to be string value
                ts = datetime.datetime.strptime(row['LocalHour'],
                    '%Y-%m-%d %H:%M').isoformat()
                if ts in self._timeprofile[event_id][day]:
                    raise ValueError("Multiple timeprofile values for %s %s",
                        row['Fire'], ts)
                self._timeprofile[event_id][day][ts] = {
                    "area_fraction": row['FractionOfDay'],
                    "flaming": row['FractionOfDay'],
                    "residual": row['FractionOfDay'],
                    "smoldering": row['FractionOfDay']
                }

            # TODO: fill in zeros for hours not specified ???
            # TODO: make sure fractions for each event/day add up to 1.0

    def _process_row(self, row):
        fire = Fire({
            "id": row.get("id") or str(uuid.uuid4()),
            "event_of": {},
            # Though unlikely, it's possible that the points in
            # a single fire span multiple time zones
            "specified_points_by_date_n_offset": defaultdict(
                lambda: defaultdict(lambda: []))
        })

        start, utc_offset = self._parse_date_time(row["date_time"])
        if not start:
            raise ValueError("Fire location missing time information")

        sp = {loc_attr: f(row.get(csv_key))
            for csv_key, loc_attr, f in LOCATION_FIELDS}
        if self._omit_nulls:
            sp = {k: v for k, v in sp.items() if v is not None}

        fire['specified_points_by_date_n_offset'][start][utc_offset].append(sp)

        # event and type could have been set when the Fire object was
        # instantiated, but checking amd setting here allow the fields to
        # be set even if only subsequent rows for the fire have them defined
        if row.get("event_id"):
            fire["event_of"]["id"] = row["event_id"]
        if row.get("event_url"):
            fire["event_of"]["url"] = row["event_url"]

        if row.get("type"):
            fire["type"] = row["type"].lower()

        # Add consumption data if present and flag active.
        # This was implemented for the Canadian version of the SmartFire system.
        # It is important to note that this consumption marshalling was done with only the Canadian format
        # in mind. If consumption is added to the input of the US system, further changes maybe required.
        if self._load_consumption:
            flaming = 0
            smold = 0
            resid = 0
            duff = 0

            if row.get("consumption_flaming") is not None:
                flaming = get_optional_float(row.get("consumption_flaming"))
            if row.get("consumption_smoldering") is not None:
                smold = get_optional_float(row.get("consumption_smoldering"))
            if row.get("consumption_residual") is not None:
                resid = get_optional_float(row.get("consumption_residual"))
            if row.get("consumption_duff") is not None:
                duff = get_optional_float(row.get("consumption_duff"))

            total_cons = flaming + smold + resid + duff


            area = sp.get('area') or 1
            consumption = {
                "flaming": [area * flaming],
                "residual": [area * resid],
                "smoldering": [area * smold],
                "duff": [area * duff],
                "total": [area * total_cons]
            }

            self._consumption_values[fire["id"]] = consumption

        # TODO: other marshaling

        return fire

    def _post_process_activity(self, fire):
        event_id = fire.get("event_of", {}).get("id")
        fire["activity"] = []
        sorted_items = sorted(fire.pop("specified_points_by_date_n_offset").items(),
            key=lambda a: a[0])
        for start, points_by_utc_offset in sorted_items:
            for utc_offset, specified_points in points_by_utc_offset.items():
                fire['activity'].append({
                    "active_areas": [
                        {
                            "start": start,
                            "end": start + ONE_DAY,
                            "utc_offset": utc_offset,
                            "specified_points": specified_points
                        }
                    ]
                })
                if event_id and (start in self._timeprofile[event_id]):
                    fire['activity'][-1]["active_areas"][0]["timeprofile"] = self._timeprofile[event_id][start]
        # Again this is for the Canadian addition. Assumes one location per fire.
        # TODO: Add check to see if fuelbed initialized.
        if fire["id"] in self._consumption_values:
            fire["activity"][-1]["active_areas"][0]["specified_points"][-1]["fuelbeds"] = [{}]
            fire["activity"][-1]["active_areas"][0]["specified_points"][-1]["fuelbeds"][0]["consumption"] = self._consumption_values[fire["id"]]


    # Note: Although 'timezone' (a numberical value) is defined alongsite
    #   date_time (which may include utc_offset), utc_offset, if defined, reflects
    #   daylight savings and thus is the true offset from UTC, whereas timezone
    #   does not change; e.g. an august 5th fire in Florida is listed with timezone
    #   -5.0 and utc_offset (embedded in the 'date_time' field) '-04:00'

    ## 'date_time'
    DATE_TIME_MATCHERS = (
        (re.compile('^(\d{12})(\d{2})?([+-]\d{2}\:\d{2})$'), "%Y%m%d%H%M"),
        (re.compile('^(\d{12})(\d{2})?Z$'), "%Y%m%d%H%M"),
        (re.compile('^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3})([+-]\d{2}\:\d{2})$'),
            "%Y-%m-%dT%H:%M:%S.%f")
    )

    def _parse_date_time(self, date_time):
        """Parses 'date_time' field, found in BSF fire data

        Note: older BSF fire data formatted the date_time field without
        local timezone information, mis-representing everything as
        UTC.  E.g.:

            '201405290000Z'

        Newer (and current) SF2 fire data formats date_time like so:

            '201508040000-04:00'

        Another newer format:

            2020-05-13T00:00:00.000-07:00

        With true utc offset embedded in the string.
        """
        start = None
        utc_offset = None

        if date_time:
            try:
                for matcher, fmt in self.DATE_TIME_MATCHERS:
                    m = matcher.match(date_time)
                    if m:
                        start = datetime.datetime.strptime(m.group(1), fmt)
                        if len(m.groups()) > 1:
                            utc_offset = parse_utc_offset(m.groups()[-1])
                        break

            except Exception as e:
                logging.warn("Failed to parse 'date_time' value %s",
                    date_time)
                logging.debug(traceback.format_exc())

        return start, utc_offset
