"""bluesky.web.api.v1.run"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import io
import json
import logging
import uuid
import tornado.web

#from bluesky.web.lib.auth import b_auth
from bluesky import modules, models, process
from bluesky.configuration import config_parser_from_dict
from bluesky.exceptions import BlueSkyImportError, BlueSkyModuleError


class RunExecuter(tornado.web.RequestHandler):
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
                includes_hysplit = ("dispersion" in modules and
                    data.get('config', {}).get('dispersion', {}).get('module') == 'hysplit')
                if includes_hysplit:
                    # TODO: CALL run_asynchrously AND RETURN TRUE RUN ID
                    #run_id = process.run_asynchrously(modules, data)
                    self.write({
                        "run_id": str(uuid.uuid1()),
                        "IS_DUMMY_DATA": True
                    })
                else:
                    fires_manager = models.fires.FiresManager()
                    fires_manager.load(data)
                    config = config_parser_from_dict(data.get('config') or {})
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
            except Exception, e:
                # IF exceptions aren't caught, the traceback is returned as
                # the response body
                logging.error('Exception: {}'.format(e))
                self.set_status(500)



## ***
## *** TODO: REPLACE DUMMY DATA WITH REAL!!!
## ***
## *** Will need to add configuration options to web service to point
## *** to source of data (e.g. url of mongodb containing the data vs.
## *** root url or path to crawl for data given run id vs. something else...)
## ***

class RunStatus(tornado.web.RequestHandler):

    def get(self, run_id):
        self.write({
            "complete": False,
            "percent": 90.0,
            "failed": False,
            "message": "This is dummy data",
            "IS_DUMMY_DATA": True
        })

class RunOutput(tornado.web.RequestHandler):

    def get(self, run_id):
        self.write({
           "output": {
               "directory": "http://smoke.airfire.org/bluesky-daily/output/standard/PNW-4km/2015082800/",
               "images": {
                   "hourly": [
                       "images/hourly/1RedColorBar/hourly_201508280000.png",
                       "images/hourly/1RedColorBar/hourly_201508280100.png",
                       "images/hourly/1RedColorBar/hourly_201508280200.png",
                       "images/hourly/1RedColorBar/hourly_201508280300.png",
                       "images/hourly/1RedColorBar/hourly_201508280400.png",
                       "images/hourly/1RedColorBar/hourly_201508280500.png",
                       "images/hourly/1RedColorBar/hourly_201508280600.png"
                   ],
                   "daily": {
                       "average": [
                           "images/daily_average/1RedColorBar/daily_average_20150828.png",
                            "images/daily_average/1RedColorBar/daily_average_20150829.png"
                       ],
                       "maximum": [
                            "images/daily_average/1RedColorBar/daily_maximum_20150828.png",
                            "images/daily_average/1RedColorBar/daily_maximum_20150829.png"
                       ],
                   }
               },
               "netCDF": "data/ smoke_dispersion.nc",
               "kmz": "smoke_dispersion.kmz",
               "fireLocations": "data/fire_locations.csv",
               "fireEvents": "data/fire_events.csv",
               "fireEmissions": "data/fire_emissions.csv"
           }
        })
