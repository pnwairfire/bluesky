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
from .api.ping import Ping
from .api.v1.domain import (
    DomainInfo as DomainInfoV1,
    DomainAvailableDates as DomainAvailableDatesV1
)
from .api.v1.run import (
    RunExecuter as RunExecuterV1,
    RunStatus as RunStatusV1,
    RunOutput as RunOutputV1
)

routes = [
    # TODO: update all patterns to allow optional trailing slash
    (r"/api/ping/?", Ping),
    (r"/api/v1/domains/?", DomainInfoV1),
    (r"/api/v1/domains/([^/]+)/?", DomainInfoV1),
    (r"/api/v1/domains/([^/]+)/available-dates/?", DomainAvailableDatesV1),
    (r"/api/v1/available-dates/?", DomainAvailableDatesV1),
    (r"/api/v1/run/?", RunExecuterV1),
    (r"/api/v1/run/([^/]+)/status/?", RunStatusV1),
    (r"/api/v1/run/([^/]+)/output/?", RunOutputV1)
]

DEFAULT_LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s %(filename)s#%(funcName)s: %(message)s"
def configure_logging(log_level_str, log_file, log_format):
    log_level = getattr(logging, log_level_str)
    logging.basicConfig(level=log_level, format=log_format)

    log_file = log_file
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(fh)

def main(port, log_level_str=None, log_file=None,
        log_format=None, debug=False):
    """Main method for starting bluesky tornado web service

    args:
     - port -- port to listen on

    kwargs:
     - log_level_str -- DEBUG, INFO, etc.
     - log_file -- file to write logs to
     - log_format -- format of log messages
     - debug -- whether or not to run in debug mode (with code
        auto-reloading etc)
    """
    log_level_str = log_level_str or 'WARNING'
    log_format = log_format or DEFAULT_LOG_FORMAT
    configure_logging(log_level_str, log_file, log_format)
    application = tornado.web.Application(routes, debug=debug)
    logging.info(' * Debug mode: {}'.format(debug))
    logging.info(' * Port: {}'.format(port))
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()
