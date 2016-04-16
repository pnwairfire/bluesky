"""Unit tests for smartfire2 csv loaders defined in bluesky.loaders.smartfire2.csv
"""

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

EXPECTED_FIRES = []

EXPECTED_FIRES_WITH_EVENTS = []

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
        events_filename = os.path.join(self._temp_dir, "fires.json")
        with open(events_filename, 'w') as f:
            f.write(EVENTS_JSON)

        l = sf2csv.FileLoader(file=filename, events_file=events_filename)
        assert l._filename == filename
        assert l._events_filename == events_filename

        fires = l.load()
        assert fires == EXPECTED_FIRES_WITH_EVENTS
