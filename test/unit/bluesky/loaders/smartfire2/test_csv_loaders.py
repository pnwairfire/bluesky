"""Unit tests for smartfire2 csv loaders defined in bluesky.loaders.smartfire2.csv
"""

import copy
import datetime
import os
import tempfile

from freezegun import freeze_time
from py.test import raises

from bluesky.loaders.smartfire2 import csv as sf2csv

FIRES_JSON = """id,event_id,latitude,longitude,type,area,date_time,slope,state,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,consumption_flaming,consumption_smoldering,consumption_residual,consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm25,pm10,co,co2,ch4,nox,nh3,so2,voc,VEG,canopy,event_url,fccs_number,sf_event_guid,sf_server,sf_stream_name,timezone
SF11C112212114042848520,SF11E726370,26.313,-77.123,RX,99.9999997516,201604120000-05:00,10.0,Unknown,Unknown,-9999,2810015000,,,,,,,,,,,,10.0,12.0,12.0,22.0,130.0,150.0,,,,,6.0,6.0,6.0,6.0,40.0,80.0,13.0,30.0,4,14,6,19,5,8,,,,,,,,,,,,,http://128.208.123.111/smartfire/events/ff7c6ee9-5f54-4fd3-bd22-ebff53b429f9,,ff7c6ee9-5f54-4fd3-bd22-ebff53b429f9,128.208.123.111,realtime,-5.0
SF11C112314714042848520,SF11E708166,41.948,-96.017,RX,99.9999997516,201604120000-05:00,10.0,IA,USA,19133,2810015000,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,10.0,12.0,12.0,22.0,130.0,150.0,0.0,0.0,0.0,0.0,6.0,6.0,6.0,6.0,40.0,80.0,13.0,30.0,4,14,6,19,5,8,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,Urban,0.0,http://128.208.123.111/smartfire/events/62a57e65-a899-436b-be2b-95ea01919c54,0,62a57e65-a899-436b-be2b-95ea01919c54,128.208.123.111,realtime,-6.0
"""

EVENTS_JSON = """id,event_name,total_area,total_heat,total_pm25,total_pm10,total_pm,total_co,total_co2,total_ch4,total_nmhc,total_nox,total_nh3,total_so2,total_voc,total_bc,total_h2,total_nmoc,total_no,total_no2,total_oc,total_tpc,total_tpm
SF11E698479,"Unnamed fire in Palm Beach County, Florida",264.7058816955166,0.0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0,0,0,0,0,0,0,0
SF11E708166,"Unnamed fire in Monona County, Iowa",99.9999997516396,0.0,0.0,0.0,0,0.0,0.0,0.0,0,0.0,0.0,0.0,0.0,0,0,0,0,0,0,0,0
"""

EXPECTED_FIRES = [
    {
        'VEG': '',
        'area': 99.9999997516,
        'canopy': '',
        'ch4': '',
        'co': '',
        'co2': '',
        'consumption_duff': '',
        'consumption_flaming': '',
        'consumption_residual': '',
        'consumption_smoldering': '',
        'country': 'Unknown',
        'date_time': '201604120000-05:00',
        'duff': '',
        'event_id': 'SF11E726370',
        'event_url': 'http://128.208.123.111/smartfire/events/ff7c6ee9-5f54-4fd3-bd22-ebff53b429f9',
        'fccs_number': '',
        'fips': -9999,
        'fuel_100hr': '',
        'fuel_10hr': '',
        'fuel_10khr': '',
        'fuel_1hr': '',
        'fuel_1khr': '',
        'fuel_gt10khr': '',
        'grass': '',
        'heat': '',
        'id': 'SF11C112212114042848520',
        'latitude': 26.313,
        'litter': '',
        'longitude': -77.123,
        'max_humid': 80.0,
        'max_temp': 30.0,
        'max_temp_hour': 14,
        'max_wind': 6.0,
        'max_wind_aloft': 6.0,
        'min_humid': 40.0,
        'min_temp': 13.0,
        'min_temp_hour': 4,
        'min_wind': 6.0,
        'min_wind_aloft': 6.0,
        'moisture_100hr': 12.0,
        'moisture_10hr': 12.0,
        'moisture_1hr': 10.0,
        'moisture_1khr': 22.0,
        'moisture_duff': 150.0,
        'moisture_live': 130.0,
        'nh3': '',
        'nox': '',
        'pm10': '',
        'pm25': '',
        'rain_days': 8,
        'rot': '',
        'scc': 2810015000,
        'sf_event_guid': 'ff7c6ee9-5f54-4fd3-bd22-ebff53b429f9',
        'sf_server': '128.208.123.111',
        'sf_stream_name': 'realtime',
        'shrub': '',
        'slope': 10.0,
        'snow_month': 5,
        'so2': '',
        'state': 'Unknown',
        'sunrise_hour': 6,
        'sunset_hour': 19,
        'timezone': -5.0,
        'type': 'RX',
        'voc': ''
    },
    {
        'VEG': 'Urban',
        'area': 99.9999997516,
        'canopy': 0.0,
        'ch4': 0.0,
        'co': 0.0,
        'co2': 0.0,
        'consumption_duff': 0.0,
        'consumption_flaming': 0.0,
        'consumption_residual': 0.0,
        'consumption_smoldering': 0.0,
        'country': 'USA',
        'date_time': '201604120000-05:00',
        'duff': 0.0,
        'event_id': 'SF11E708166',
        'event_url': 'http://128.208.123.111/smartfire/events/62a57e65-a899-436b-be2b-95ea01919c54',
        'fccs_number': 0,
        'fips': 19133,
        'fuel_100hr': 0.0,
        'fuel_10hr': 0.0,
        'fuel_10khr': 0.0,
        'fuel_1hr': 0.0,
        'fuel_1khr': 0.0,
        'fuel_gt10khr': 0.0,
        'grass': 0.0,
        'heat': 0.0,
        'id': 'SF11C112314714042848520',
        'latitude': 41.948,
        'litter': 0.0,
        'longitude': -96.017,
        'max_humid': 80.0,
        'max_temp': 30.0,
        'max_temp_hour': 14,
        'max_wind': 6.0,
        'max_wind_aloft': 6.0,
        'min_humid': 40.0,
        'min_temp': 13.0,
        'min_temp_hour': 4,
        'min_wind': 6.0,
        'min_wind_aloft': 6.0,
        'moisture_100hr': 12.0,
        'moisture_10hr': 12.0,
        'moisture_1hr': 10.0,
        'moisture_1khr': 22.0,
        'moisture_duff': 150.0,
        'moisture_live': 130.0,
        'nh3': 0.0,
        'nox': 0.0,
        'pm10': 0.0,
        'pm25': 0.0,
        'rain_days': 8,
        'rot': 0.0,
        'scc': 2810015000,
        'sf_event_guid': '62a57e65-a899-436b-be2b-95ea01919c54',
        'sf_server': '128.208.123.111',
        'sf_stream_name': 'realtime',
        'shrub': 0.0,
        'slope': 10.0,
        'snow_month': 5,
        'so2': 0.0,
        'state': 'IA',
        'sunrise_hour': 6,
        'sunset_hour': 19,
        'timezone': -6.0,
        'type': 'RX',
        'voc': 0.0
    }
]

EXPECTED_FIRES_WITH_EVENTS = copy.deepcopy(EXPECTED_FIRES)
EXPECTED_FIRES_WITH_EVENTS[1]['name'] = "Unnamed fire in Monona County, Iowa"

class TestSmartfire2CsvFileLoader(object):

    def setup(self):
        self._temp_dir = tempfile.mkdtemp()

    def test_no_events(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with open(filename, 'w') as f:
            f.write(FIRES_JSON)

        l = sf2csv.FileLoader(file=filename)
        assert l._filename == filename
        assert l._events_filename == None

        fires = l.load()
        assert fires == EXPECTED_FIRES

    def test_with_events(self):
        filename = os.path.join(self._temp_dir, "fires.json")
        with open(filename, 'w') as f:
            f.write(FIRES_JSON)
        events_filename = os.path.join(self._temp_dir, "events.json")
        with open(events_filename, 'w') as f:
            f.write(EVENTS_JSON)

        l = sf2csv.FileLoader(file=filename, events_file=events_filename)
        assert l._filename == filename
        assert l._events_filename == events_filename

        fires = l.load()
        assert fires == EXPECTED_FIRES_WITH_EVENTS
