"""bluesky.web.api.v1.run"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import io
import json
import logging
import tornado.web

#from bluesky.web.lib.auth import b_auth
from bluesky import modules, models, process
from bluesky.configuration import config_from_dict
from bluesky.exceptions import BlueSkyImportError, BlueSkyModuleError


class Run(tornado.web.RequestHandler):
    # def _bad_request(self, msg):
    #     self.set_status(400)
    #     self.write({"error": msg})

    def post(self):
        if not self.request.body:
            self.set_status(400, 'Bad request: empty post data')
            return

        data = json.loads(self.request.body)
        if "modules" not in data:
            self.set_status(400, "Bad request: 'modules' not specified")
        elif "fire_information" not in data:
            self.set_status(400, "Bad request: 'fire_information' not specified")
        else:
            try:
                modules = data.pop('modules')
                fires_manager = models.fires.FiresManager()
                fires_manager.load(data)
                config = config_from_dict(data.get('config') or {})

                try:
                    process.run_modules(modules, fires_manager, config)
                except BlueSkyModuleError, e:
                    # Exception was caught while running modules and added to
                    # fires_manager's meta data, and so will be included in
                    # the output data
                    # TODO: should module error not be reflected in http error status?
                    pass
                except BlueSkyImportError, e:
                    self.set_status(400, "Bad request: {}".format(e.message))
                except Exception, e:
                    logging.error('Exception: {}'.format(e))
                    self.set_status(500)

                # If you pass a dict into self.write, it will dump it to json and set
                # content-type to json;  we need to specify a json encoder, though, so
                # we'll manaually set the header adn dump the json
                self.set_header('Content-Type', 'application/json') #; charset=UTF-8')
                fires_manager.dumps(output_stream=self)
            except:
                # IF exceptions aren't caught, the traceback is returned as
                # the response body
                self.set_status(500)
