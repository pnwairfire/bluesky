"""bluesky.extrafilewriters.emissionscsv

Writes fire emissions csv file in the form:

    fire_id,hour,ignition_date_time,date_time,area_fract,flame_profile,smolder_profile,residual_profile,pm25_emitted,pm10_emitted,co_emitted,co2_emitted,ch4_emitted,nox_emitted,nh3_emitted,so2_emitted,voc_emitted,pm25_flame,pm10_flame,co_flame,co2_flame,ch4_flame,nox_flame,nh3_flame,so2_flame,voc_flame,pm25_smold,pm10_smold,co_smold,co2_smold,ch4_smold,nox_smold,nh3_smold,so2_smold,voc_smold,pm25_resid,pm10_resid,co_resid,co2_resid,ch4_resid,nox_resid,nh3_resid,so2_resid,voc_resid,smoldering_fraction,heat,percentile_000,percentile_005,percentile_010,percentile_015,percentile_020,percentile_025,percentile_030,percentile_035,percentile_040,percentile_045,percentile_050,percentile_055,percentile_060,percentile_065,percentile_070,percentile_075,percentile_080,percentile_085,percentile_090,percentile_095,percentile_100
    SF11C38780083219874810,0,201803170000-08:00,201803170000-08:00,0.0057,0.0057,0.0057,0.0057,0.009475,0.011181,0.10173,1.720376,0.005177,0.00232,0.001688,0.001049,0.024262,0.006488,0.007655,0.063984,1.470124,0.003404,0.002157,0.001075,0.000873,0.015454,0.001597,0.001885,0.02018,0.133793,0.000948,8.7e-05,0.000328,9.4e-05,0.004709,0.00139,0.001641,0.017566,0.116459,0.000825,7.6e-05,0.000285,8.2e-05,0.004099,0.981589,193672.799534,1.937531,2.07856035,2.2195897,2.36061905,2.5016484,2.64267775,2.7837071,2.92473645,3.0657658,3.20679515,3.3478245,3.48885385,3.6298832,3.77091255,3.9119419,4.05297125,4.1940006,4.33502995,4.4760593,4.61708865,4.758118
    SF11C38780083219874810,1,201803170000-08:00,201803170100-08:00,0.0057,0.0057,0.0057,0.0057,0.009475,0.011181,0.10173,1.720376,0.005177,0.00232,0.001688,0.001049,0.024262,0.006488,0.007655,0.063984,1.470124,0.003404,0.002157,0.001075,0.000873,0.015454,0.001597,0.001885,0.02018,0.133793,0.000948,8.7e-05,0.000328,9.4e-05,0.004709,0.00139,0.001641,0.017566,0.116459,0.000825,7.6e-05,0.000285,8.2e-05,0.004099,0.981589,193672.799534,1.937531,2.0958799,2.2542288,2.4125777,2.5709266,2.7292755,2.8876244,3.0459733,3.2043222,3.3626711,3.52102,3.6793689,3.8377178,3.9960667,4.1544156,4.3127645,4.4711134,4.6294623,4.7878112,4.9461601,5.104509
    SF11C38780083219874810,2,201803170000-08:00,201803170200-08:00,0.0057,0.0057,0.0057,0.0057,0.009475,0.011181,0.10173,1.720376,0.005177,0.00232,0.001688,0.001049,0.024262,0.006488,0.007655,0.063984,1.470124,0.003404,0.002157,0.001075,0.000873,0.015454,0.001597,0.001885,0.02018,0.133793,0.000948,8.7e-05,0.000328,9.4e-05,0.004709,0.00139,0.001641,0.017566,0.116459,0.000825,7.6e-05,0.000285,8.2e-05,0.004099,0.987726,129115.199689,1.937531,2.04076465,2.1439983,2.24723195,2.3504656,2.45369925,2.5569329,2.66016655,2.7634002,2.86663385,2.9698675,3.07310115,3.1763348,3.27956845,3.3828021,3.48603575,3.5892694,3.69250305,3.7957367,3.89897035,4.002204
    ...
"""

import csv
import logging
import os

from afdatetime import parsing as datetime_parsing
from blueskykml import smokedispersionkml

from bluesky import locationutils
from bluesky.exceptions import BlueSkyConfigurationError


BLUESKYKML_DATE_FORMAT = smokedispersionkml.FireData.date_time_format

# as of blueskykml v0.2.5, this list is:
#  'pm25', 'pm10', 'co', 'co2', 'ch4', 'nox', 'nh3', 'so2', 'voc'
# Note that blueskykml expects 'pm25', not 'pm2.5'
BLUESKYKML_SPECIES_LIST = [s.upper() for s in smokedispersionkml.FireData.emission_fields]
if 'NOX' in BLUESKYKML_SPECIES_LIST:
    BLUESKYKML_SPECIES_LIST.remove('NOX')
    BLUESKYKML_SPECIES_LIST.append('NOx')

##
## Functions for extracting fire *location * information to write to csv files
##
## Note: The growth object (arg 'g') is ignored in most of these methods.
##  It's only needed for the start time and area calculation
##

def _pick_representative_fuelbed(fire, g):
    sorted_fuelbeds = sorted(g.get('fuelbeds', []),
        key=lambda fb: fb['pct'], reverse=True)
    if sorted_fuelbeds:
        return sorted_fuelbeds[0]['fccs_id']

def _get_heat(fire, g):
    if g.get('fuelbeds'):
        heat = [fb.get('heat', {}).get('total') for fb in g['fuelbeds']]
        # non-None value will be returned if species is defined for all fuelbeds
        if not any([v is None for v in heat]):
            # heat is array of arrays
            return sum([sum(h) for h in heat])

def _get_emissions_species(species):
    def f(fire, g):
        if g.get('fuelbeds'):
            species_array = []
            for fb in g['fuelbeds']:
                total = fb.get('emissions', {}).get('total', {})
                # Try species as is, as all lowercase, and as all uppercase
                # append even if not defined, since we check bdlow if all or none
                species_array.append(
                    total.get(species) or total.get(species.lower()) or total.get(species.upper())
                )
            # non-None value will be returned if species is defined for all fuelbeds
            if not any([v is None for v in species_array]):
                return sum([sum(a) for a in species_array])
    return f

def _get_location_value(key, is_float):
    def f(fire, g):
        val = g['location'].get(key)
        if val:
            return float(val) if is_float else val
    return f

# Fire locations csv columns from BSF:
#  id,event_id,latitude,longitude,type,area,date_time,elevation,slope,
#  state,county,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,
#  fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,
#  moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,
#  consumption_flaming,consumption_smoldering,consumption_residual,
#  consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,
#  min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,
#  sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm25,pm10,co,co2,
#  ch4,nox,nh3,so2,voc,canopy,event_url,fccs_number,owner,sf_event_guid,
#  sf_server,sf_stream_name,timezone,veg
FIRE_LOCATIONS_CSV_FIELDS = (
    [
        ('id', lambda f, g: f.id),
        ('event_id', lambda f, g: f.get('event_of', {}).get('id')),
        ('latitude', lambda f, g: locationutils.LatLng(g['location']).latitude),
        ('longitude', lambda f, g: locationutils.LatLng(g['location']).longitude),
        # Note: We're keeping the 'type' field consistent with the csv files
        #   generated by smartfire, which use 'RX' and 'WF'
        ('type', lambda f, g: 'RX' if f.type == 'rx' else 'WF'),
        ('date_time', lambda f, g: datetime_parsing.parse(g['start']).strftime(BLUESKYKML_DATE_FORMAT)),
        ('event_name', lambda f, g: f.get('event_of', {}).get('name')),
        ('fccs_number', _pick_representative_fuelbed),

        #(which we're now ingesting)
        # TDOO: add 'VEG'? (Note: sf2 has 'veg' field, which we're *not* ingesting,
        #   since it seems to be a fuelbed discription which is probably for
        #   the one fccs id in the sf2 feed. This single fccs id and its description
        #   don't necesasrily represent the entire fire area, which could have
        #   multiple fuelbeds, so ingestion ignores it.  we could set 'VEG' to
        #   a concatenation of the fuelbeds or the one one making up the largest
        #   fraction of the fire.)
        ('heat', _get_heat)
    ]
    # emissions
    + [
        (s.lower(), _get_emissions_species('PM2.5' if s is 'pm25' else s))
            for s in BLUESKYKML_SPECIES_LIST if s
    ]
    # float value location fields
    + [
        (k,  _get_location_value(k, True)) for k in [
            'area', 'elevation', 'slope',
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
        ]
    ]
    # string value location fields
    + [
        (k, _get_location_value(k, False)) for k in [
            'state', 'county', 'country'
        ]
    ]
    # TODO: Add other fields if users want them
    # TODO: add other sf2 fields which we are *not* currently ingesting
    #    'fuel_1hr', 'fuel_10hr', 'fuel_100hr',
    #    'fuel_1khr', 'fuel_10khr', 'fuel_gt10khr'
    #    'canopy','shrub','grass','rot','duff', 'litter', 'VEG',
    #    'consumption_flaming', 'consumption_smoldering',
    #    'consumption_residual', 'consumption_duff', 'heat',
    #    'owner','sf_event_guid','sf_server','sf_stream_name','fips','scc'
)
"""List of fire location csv fields, with function to extract from fire object"""


##
## Functions for extracting fire *event* information to write to csv files
##

def _assign_event_name(event, fire, new_fire):
    name = fire.get('event_of', {}).get('name')
    if name:
        if event.get('name') and name != event['name']:
            logging.warn("Fire {} event name conflict: '{}' != '{}'".format(
                fire.id, name, event['name']))
        event['name'] = name

def _update_event_area(event, fire, new_fire):
    if any([not g.get('location', {}).get('area') for g in fire.growth]):
        raise ValueError("Fire {} lacks area".format(fire.get('id')))
    return event.get('total_area', 0.0) + sum([g['location']['area'] for g in fire.growth])

def _update_total_heat(event, fire, new_fire):
    if 'total_heat' in event and event['total_heat'] is None:
        # previous fire didn't have heat defined; abort so
        # that we don't end up with misleading partial heat
        return
    logging.debug("total fire heat: %s", new_fire.get('heat'))
    if new_fire.get('heat'):
        return event.get('total_heat', 0.0) + new_fire['heat']

def _update_total_emissions_species(species):
    key = 'total_{}'.format(species)
    def f(event, fire, new_fire):
        if key in event and event[key] is None:
            # previous fire didn't have this emissions value defined; abort so
            # that we don't end up with misleading partial total
            return

        if new_fire.get(species):
            return event.get(key, 0.0) + new_fire[species]
    return f

# Fire events csv columns from BSF:
#  id,event_name,total_area,total_heat,total_pm25,total_pm10,total_pm,
#  total_co,total_co2,total_ch4,total_nmhc,total_nox,total_nh3,total_so2,
#  total_voc,total_bc,total_h2,total_nmoc,total_no,total_no2,total_oc,
#  total_tpc,total_tpm
FIRE_EVENTS_CSV_FIELDS = [
    ('event_name', _assign_event_name),
    ('total_heat', _update_total_heat),
    ('total_area', _update_event_area),
    ('total_nmhc', _update_total_emissions_species('nmhc'))
] + [
    ('total_{}'.format(s.lower()), _update_total_emissions_species(s.lower()))
        for s in BLUESKYKML_SPECIES_LIST
]
"""List of fire event csv fields, with function to extract from fire object
and aggregate.  Note that this list lacks 'id', which is the first column.
"""

##
## Writer class
##

class FiresCsvsWriter(object):

    def __init__(self, dest_dir, **config):
        fl = config.get('fire_locations_filename') or 'fire_locations.csv'
        self._fire_locations_filename = os.path.join(dest_dir, fl)

        fe = config.get('fire_events_filename') or 'fire_events.csv'
        self._fire_events_filename = os.path.join(dest_dir, fe)

    def write(self, fires_manager):
        fires, events = self._collect_csv_fields()
        with open(fire_locations_csv_pathname, 'w') as _f:
            f = csv.writer(_f)
            f.writerow([k for k, l in FIRE_LOCATIONS_CSV_FIELDS])
            for fire in fires:
                f.writerow([str(fire[k] or '') for k, l in FIRE_LOCATIONS_CSV_FIELDS])

        with open(fire_events_csv_pathname, 'w') as _f:
            f = csv.writer(_f)
            f.writerow(['id'] + [k for k, l in FIRE_EVENTS_CSV_FIELDS])
            for e_id, event in list(events.items()):
                f.writerow([e_id] +
                    [str(event[k] or '') for k, l in FIRE_EVENTS_CSV_FIELDS])

    def _collect_csv_fields(self):
        # As we iterate through fires, collecting necessary fields, collect
        # events information as well
        fires = []
        events = {}
        for fire in self._fires:
            for g in fire.growth:
                fires.append({k: l(fire, g) or '' for k, l in FIRE_LOCATIONS_CSV_FIELDS})
            event_id = fire.get('event_of', {}).get('id')
            if event_id:
                events[event_id] = events.get(event_id, {})
                for k, l in FIRE_EVENTS_CSV_FIELDS:
                    events[event_id][k] = l(events[event_id], fire, fires[-1])
        logging.debug("events: %s", events)
        return fires, events
