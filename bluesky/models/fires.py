"""tasks.takedown - fabric tasks for ....
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import csv
import json
import sys

__all__ = [
    'FireDataFormats',
    'FireDataFormatNotSupported',
    'Fire'
]


class FireDataFormatNotSupported(ValueError):
    pass

class FireDataFormats(object):
    _formats = {
        'json': 1,
        'csv': 2
    }
    _r_formats = dict([(v,k) for k,v in _formats.items()])

    # To handle missing classes methods and attributes
    class __metaclass__(type):
        def __getattr__(cls, attr):
            if attr == 'formats':
                return cls._formats.keys()
            if cls._formats.has_key(attr.lower()):
                return cls._formats[attr.lower()]
            raise FireDataFormatNotSupported(
                "%s is not a valid fire data format" % (attr))

    @classmethod
    def get_format_str(cls, format_id):
        return cls._r_formats.get(format_id)

class Fire(dict):

    def __init__(self, *args, **kwargs):
        super(Fire, self).__init__(*args, **kwargs)

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]
        raise KeyError

    @classmethod
    def from_json(cls, stream):
        """Returns array of Fire objects loaded from json

        Always returns an array, even if json input represents a single fire
        object

        Args:
         - stream -- file object or other iterable object

        TODO:
         - support already parsed JSON (i.e. dict or array)
        """
        data = json.loads(''.join([d for d in stream]))
        if hasattr(data, 'keys'):
            return [cls(data)]
        elif hasattr(data, 'append'):
            return [cls(d) for d in data]
        else:
            raise ValueError("Invalid fire json data")

    def from_csv(cls, stream):
        fires = []
        headers = None
        for row in csv.reader(stream):
            if headers:
                headers = dict([(i, row[i]) for i in xrange(len(row))])
            else:
                fires.append(cls(dict([(headers[i], row[i]) for i in xrange(len(row))])))
        return fires

    ## IO

    @classmethod
    def open(cls, options): #, do_strip_newlines):
        lines = []
        if options.input_file:
            return open(options.input_file)
        else:
            return sys.stdin

    @classmethod
    def write(cls, options, data):
        if output_file:
            with open(output_file, "w") as f:
                f.write(data)
        else:
            sys.stdout.write(data)

    @classmethod
    def loads(cls, options, format=FireDataFormats.JSON):
        loader = getattr(cls, "from_%s" % (FireDataFormats.get_format_str(format)), None)
        if not loader:
            raise FireDataFormatNotSupported
        return loader(open(options))

    @classmethod
    def dumps(cls, fires_array, output_file=None, format=FireDataFormats.JSON):
        if format == FireDataFormats.JSON:
            data = json.dumps([f.to_dict() for f in fires_array])
        elif format == FireDataFormats.CSV:
            # TDOO: implement
            raise NotImplementedError
        else:
            raise FireDataFormatNotSupported

        cls.write(options, data)
