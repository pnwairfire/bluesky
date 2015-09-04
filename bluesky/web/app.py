"""bluesky.web.app"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from flask import Flask
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)

from .api.run import Run
api.add_resource(run, '/run')
api.add_resource(run, '/run/')

if __name__ == '__main__':
    app.run(debug=True)
