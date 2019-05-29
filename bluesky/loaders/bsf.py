"""bluesky.loaders.bsf

BSF csv structure

id,event_id,latitude,longitude,type,area,date_time,slope,state,county,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,consumption_flaming,consumption_smoldering,consumption_residual,consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm25,pm10,co,co2,ch4,nox,nh3,so2,voc,VEG,canopy,event_url,fccs_number,owner,sf_event_guid,sf_server,sf_stream_name,timezone
SF11C77574457421602580,SF11E4146026,27.188,-81.113,RX,67.999999831,201905280000-04:00,10.0,FL,,USA,12043,2810015000,0.5,0.25,0.25,0.0,0.0,0.0,2.2,0.0,1.0,0.0,1.0,10.0,12.0,12.0,22.0,130.0,150.0,4.48236738577,0.430136575756,0.332945533864,0.0,6.0,6.0,6.0,6.0,40.0,80.0,13.0,30.0,4,14,6,19,5,8,710946484.545042,3.0819790000000005,3.6367379999999994,32.78775999999999,575.1165699999999,1.676383,0.784719,0.5446900000000001,0.349551,7.829838999999999,Default Unknown Fuel Type,0.0,http://128.208.123.111/smartfire/events/f037f5b4-01c3-4223-bee4-8dfc0e7b9967,0,,f037f5b4-01c3-4223-bee4-8dfc0e7b9967,128.208.123.111,realtime,-5.0

"""

__author__ = "Joel Dubowy"

import datetime
import logging
import traceback
import uuid
from collections import defaultdict

from bluesky.models.fires import Fire
from . import BaseCsvFileLoader
from bluesky.datetimeutils import parse_datetime, parse_utc_offset

__all__ = [
    'CsvFileLoader'
]


##
## Loader Classes
##

ONE_DAY = datetime.timedelta(days=1)

class CsvFileLoader(BaseCsvFileLoader):

    def __init__(self, **config):
        super().__init__(**config)
        self._skip_failures = config.get('skip_failures')

    def _marshal(self, data):
        self._headers = data[0]
        self._fires = {}

        for row in data[1:]:
            try:
                self._process_row(row)

            except Exception as e:
                if not self._skip_failures:
                    logging.debug(traceback.format_exc())
                    raise ValueError(str(e))
                # else, just log str(e) (which is detailed enough)
                logging.warning(str(e))

        self._post_process_activity()

        return list(self._fires.values())

    def _process_row(self, row):
        fire_id = row.get("id") or str(uuid.uuid4())
        if fire_id not in self._fires:
            self._fires[fire_id] = Fire({
                "id": fire_id,
                "specified_points_by_date": defaultdict(lambda: [])
            })
        start = parse_datetime(row["date_time"][:8])

        self._fires[fire_id]['specified_points_by_date'][start].append({
            "lat": row["latitude"],
            "lng": row["longitude"],
            "utc_offset": parse_utc_offset(row["date_time"][12:]),
            "area": row["area"]
        })

        if row.get("event_id"):
            self._fires[fire_id]["event_of"] = {
                "id": row["event_id"]
            }

        # TODO: other marshaling

    def _post_process_activity(self):
        for fire in self._fires.values():
            fire["activity"] = []
            for start, specified_points in fire.pop("specified_points_by_date").items():
                fire['activity'].append({
                    "active_areas": [
                        {
                            "start": start,
                            "end": start + ONE_DAY,
                            "specified_points": specified_points
                        }
                    ]
                })
