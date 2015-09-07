"""bluesky.web.api.v1.run"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import io
import json
import tornado.web

#from bluesky.web.lib.auth import b_auth
from bluesky import modules, models

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
        elif "fires" not in data:
            self.set_status(400, "Bad request: 'fires' not specified")
        else:
            # TODO: share code that's in ./bin/bsp, first moving it somewhere in bluesky package
            fires = [models.fires.Fire(f) for f in data['fires']]
            modules = [
                importlib.import_module('bluesky.modules.%s' % (m)) for m in data['modules']
            ]
            config = data.get('config') or {}
            for module in modules:
                module.run(fires, config)
            self.write({"fires":fires})
