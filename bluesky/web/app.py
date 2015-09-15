"""bluesky.web.app"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import tornado.ioloop
import tornado.web

from . import config
from .api.v1.run import Run

routes = [
    (r"/api/v1/run/", Run),
]
application = tornado.web.Application(routes, debug=config.DEBUG)

tornado
setup_logger(application)

def main():
    application.listen(
        8888
    )
    tornado.ioloop.IOLoop.current().start()
