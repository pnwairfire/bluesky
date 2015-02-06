"""tasks.takedown - fabric tasks for ....
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import json
import sys

__all__ = [
    'FireDataFormat',
    'FireDataFormatNotSupported',
    'Fire'
]


class FireDataFormatNotSupported(ValueError):
    pass

class FireDataFormat(object):
    _formats = {
        'json': 1,
        'csv': 2
    }

    @classmethod
    def __getattr__(cls, name):
        if cls._formats.has_key(name.lower()):
            return cls._formats[name.lower()]
        raise FireDataFormatNotSupported(
            "%s is not a valid fire data format" % (name))


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

        TODO:
         - support already parsed JSON (i.e. dict or array)
        """
        data = json.loads(json_data)
        if hasattr(data, 'keys'):
            return [Fire(**data)]
        elif hasattr(data, 'append'):
            return [Fire(**d) for d in data]
        else:
            raise ValueError("Invalid fire json data")

    def from_csv(cls, csv_data):
        # TDOO: implement
        raise NotImplementedError

    ## IO

    @classmethod
    def read(cls, options, do_strip_newlines):
        lines = []
        if options.input_file:
            with open(options.input_file) as f:
                lines = f.readlines()
                data_str = "".join()
        else:
            lines = [l for l in sys.stdin]

        if do_strip_newlines:
            lines = [l.strip() for l in lines]

        return "".join(lines)

    @classmethod
    def write(cls, options, data):
        if output_file:
            with open(output_file, "w") as f:
                f.write(data)
        else:
            sys.stdout.write(data)

    @classmethod
    def loads(cls, options, format=FireDataFormat.JSON):
        if format == FireDataFormat.JSON:
            fires = cls.from_json(read(options, True))
        elif format == FireDataFormat.CSV:
            fires = cls.from_csv(read(options, False))
        else:
            raise FireDataFormatNotSupported
        return fires

    @classmethod
    def dumps(cls, fires_array, output_file=None, format=FireDataFormat.JSON):
        if format == FireDataFormat.JSON:
            data = json.dumps([f.to_dict() for f in fires_array])
        elif format == FireDataFormat.CSV:
            # TDOO: implement
            raise NotImplementedError
        else:
            raise FireDataFormatNotSupported

        cls.write(options, data)
