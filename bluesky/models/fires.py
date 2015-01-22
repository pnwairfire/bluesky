"""tasks.takedown - fabric tasks for ....
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import json
import sys

class Fire(object):
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.lat = kwargs.get("lat")
        self.lng = kwargs.get("lng")
        self.area = kwargs.get("area")
        # TODO: add other fields

    def to_dict(self):
        # TODO: dump via inspecting self rather than explicitly
        # specifying keys/values
        return {
            "id": self.id,
            "lat": self.lat,
            "lng": self.lng,
            "area": self.area
            # TODO: add other fields
        }

    @classmethod
    def from_json(cls, json_data):
        """Returns of Fire objects loaded from json

        Always returns an array, even if json input represents a single fire
        object

        Args:
         - json_data (str) -- json formated fire data
        """
        data = json.loads(json_data)
        if hasattr(data, 'keys'):
            return [Fire(**data)]
        elif hasattr(data, 'append'):
            return [Fire(**d) for d in data]
        else:
            raise ValueError("Invalid fire json data")

    ## IO

    @classmethod
    def loads(cls, options):
        if options.input_file:
            with open(options.input_file) as f:
                j = "".join([l.strip() for l in f.readlines()])
        else:
            j = "".join([l.strip() for l in sys.stdin])

        fires = cls.from_json(j)
        return fires

    @classmethod
    def dumps(cls, fires_array, output_file=None):
        json_data = json.dumps([f.to_dict() for f in fires_array])
        if output_file:
            with open(output_file, "w") as f:
                f.write(json_data)
        else:
            sys.stdout.write(json_data)
