"""bluesky.web.app"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import tornado.ioloop
import tornado.web

from .api.v1.run import Run
application = tornado.web.Application([
    (r"/api/v1/run/", Run),
])

if __name__ == '__main__':
    application.listen(8888)
    tornado.ioloop.IOLoop.current().start()
