"""tasks.takedown - fabric tasks for ....
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import json

class Fire(object):
    def __init__(self, kwargs):
        pass

    @classmethod
    def from_json(json_data):
        data = json.loads(json_data):
        if hasattr(data, 'keys'):
            return Fire(**data)
        elif hasattr(data, 'append'):
            return [Fire(**d) for d in data]
        else:
            raise ValueError("Invalid fire json data")
