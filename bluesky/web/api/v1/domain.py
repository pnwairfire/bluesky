"""bluesky.web.api.v1.domain"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import tornado.web

class DomainInfo(tornado.web.RequestHandler):

    def get(self, domain_id=None):
        self.set_status(501, "domain info not yet implemented")
