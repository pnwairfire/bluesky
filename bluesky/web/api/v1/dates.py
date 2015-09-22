"""bluesky.web.api.v1.dates"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import tornado.web

class AvailableDates(tornado.web.RequestHandler):

    def get(self, domain_id=None):
        self.set_status(501, "available dates not yet implemented")
