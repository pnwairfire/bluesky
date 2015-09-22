"""bluesky.web.api.v1.domain"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import tornado.web


## *** TODO: REPLACE DUMMY DATA WITH REAL!!! **



class DomainInfo(tornado.web.RequestHandler):

    DUMMY_DOMAIN_DATA = {
        "PNW-4km": {
            "dates": [
                datetime.date.today().strftime("%Y%m%d"),
                (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d"),
                (datetime.date.today() - datetime.timedelta(2)).strftime("%Y%m%d")
            ],
            "boundary": {
                "center_latitude": 45.0,
                "center_longitude": -118.3,
                "width_longitude": 20.0,
                "height_latitude": 10.0
            },
            "IS_DUMMY_DATA": True
        },
        "CANSAC-6km": {
            "dates": [
                datetime.date.today().strftime("%Y%m%d"),
                (datetime.date.today() - datetime.timedelta(1)).strftime("%Y%m%d"),
                (datetime.date.today() - datetime.timedelta(2)).strftime("%Y%m%d")
            ],
            "boundary": {
                "center_latitude": 36.5,
                "center_longitude": -119.0,
                "width_longitude": 25.0,
                "height_latitude": 17.5
            },
            "IS_DUMMY_DATA": True
        }
    }

    def get(self, domain_id=None):
        if not domain_id:
            self.write(self.DUMMY_DOMAIN_DATA)
        elif domain_id in self.DUMMY_DOMAIN_DATA:
            self.write(self.DUMMY_DOMAIN_DATA[domain_id])
        else:
            self.set_status(404, "Domain does not exist")
