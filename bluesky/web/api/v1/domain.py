"""bluesky.web.api.v1.domain"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import json
import tornado.web

## ***
## *** TODO: REPLACE DUMMY DATA WITH REAL!!!
## ***
## *** Will need to add configuration options to web service to point
## *** to source of data (e.g. url of mongodb containing the data vs.
## *** root url or path to crawl for data vs. something else...)
## ***

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

class DomainInfo(tornado.web.RequestHandler):

    def get(self, domain_id=None):
        if not domain_id:
            self.write(DUMMY_DOMAIN_DATA)
        elif domain_id in DUMMY_DOMAIN_DATA:
            self.write(DUMMY_DOMAIN_DATA[domain_id])
        else:
            self.set_status(404, "Domain does not exist")


class DomainAvailableDates(tornado.web.RequestHandler):

    def get(self, domain_id):
        if domain_id in DUMMY_DOMAIN_DATA:
            # We need to dump the dates array to json and explicitly set the
            # content type (to json) - something that RequestHandler.write does
            # for bytes, unicode, and dict objects - beacuse lists are not
            # accepted by RequestHandler.write (for security reasons)
            self.set_header('Content-Type', 'application/json') #; charset=UTF-8')
            self.write(json.dumps(DUMMY_DOMAIN_DATA[domain_id]["dates"]))
        else:
            self.set_status(404, "Domain does not exist")
