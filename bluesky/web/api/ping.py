"""bluesky.web.api.v1.run"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import tornado.web

__all__ = [
    'Ping'
]

class Ping(tornado.web.RequestHandler):

    def get(self):
        # TODO: return anything else?
        self.write({"msg": "pong"})
