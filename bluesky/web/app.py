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

def main(port, debug=False):
    """Main method for starting bluesky tornado web service

    args:
     - port -- port to listen on

    kwargs:
     - debug -- whether or not to run in debug mode (with code
        auto-reloading etc)

    Note that calling code is responsible for configuring logging
    """
    application = tornado.web.Application(routes, debug=debug)
    logging.info(' * Debug mode: {}'.format(debug))
    logging.info(' * Port: {}'.format(port))
    application.listen(port)
    tornado.ioloop.IOLoop.current().start()
