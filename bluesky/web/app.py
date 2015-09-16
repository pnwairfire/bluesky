"""bluesky.web.app"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import ConfigParser
import tornado.ioloop
import tornado.web

from . import config
from .api.v1.run import Run

routes = [
    (r"/api/v1/run/", Run),
]

def get_config_value(config, section, key, default):
    try:
        return config.get(section, key)
    except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
        return default

def main(config, debug=False):
    """Main method for starting bluesky tornado web service

    args:
     - config -- configparser object

    kwargs:
     - debug -- whether or not to run in debug mode (with code
        auto-reloading etc)
    """
    application = tornado.web.Application(routes, debug=debug)

    port = get_config_value(config, 'server', 'port', 8888)
    #host = get_config_value(config, 'server', 'host', "localhost")

    # TODO: set up / confgure logging

    application.listen(
        port#,host=config.HOST
    )

    tornado.ioloop.IOLoop.current().start()
