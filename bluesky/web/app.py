"""bluesky.web.app"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import logging
import tornado.ioloop
#import tornado.log
import tornado.web

from bluesky.configuration import get_config_value
# TODO: use path args for version and api module. ex:
#  routes = [
#    ('/api/<api_version:[^/]+>/<api_module:[^/]+>/'), Dispatcher
#  ]
# and have dispatcher try to dynamically import and run the
# appropriate hander, returning 404 if not implemented
from .api.v1.run import Run as RunV1

routes = [
    (r"/api/v1/run/", RunV1),
]

LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(filename)s#%(funcName)s: %(message)s"
def configure_logging(config):
    log_level = getattr(logging, get_config_value(config, 'logging', 'level', 'WARNING'))
    logging.basicConfig(level=log_level, format=LOG_FORMAT)

    log_file = get_config_value(config, 'logging', 'file')
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(LOG_FORMAT))
        logging.getLogger().addHandler(fh)

def main(config, debug=False):
    """Main method for starting bluesky tornado web service

    args:
     - config -- configparser object

    kwargs:
     - debug -- whether or not to run in debug mode (with code
        auto-reloading etc)
    """
    application = tornado.web.Application(routes, debug=debug)

    port = int(get_config_value(config, 'server', 'port', 8888))
    #host = get_config_value(config, 'server', 'host', "localhost")

    configure_logging(config)

    logging.info(' * Debug mode: {}'.format(debug))
    logging.info(' * Port: {}'.format(port))

    application.listen(
        port #,host=config.HOST
    )

    tornado.ioloop.IOLoop.current().start()
