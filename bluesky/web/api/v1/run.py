"""bluesky.web.api.v1.run"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import tornado.ioloop

#from bluesky.web.lib.auth import b_auth
from bluesky import modules, models

class Run(tornado.web.RequestHandler):

    def post(self):
        # module = GET MODILE FROM REQUEST
        # r = CALL BSP
        # self.write(r)
        self.write('hello')
