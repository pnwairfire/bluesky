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

class FiresImporter(object):

    def __init__(self, input_file=None, output_file=None):
        self._input_file = input_file
        self._output_file = output_file
        self._fires = None

    def _from_json(self, stream):
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
            return [Fire(data)]
        elif hasattr(data, 'append'):
            return [Fire(d) for d in data]
        else:
            raise ValueError("Invalid fire json data")

    def _from_csv(self, stream):
        fires = []
        headers = None
        for row in csv.reader(stream):
            if not headers:
                headers = dict([(i, row[i]) for i in xrange(len(row))])
            else:
                fires.append(Fire(dict([(headers[i], row[i]) for i in xrange(len(row))])))
        return fires

    ## IO

    def _stream(self, file_name, flag): #, do_strip_newlines):
        if file_name:
            return open(file_name, flag)
        else:
            if flag == 'r':
                return sys.stdin
            else:
                return sys.stdout

    ## 'Public' Methods

    @property
    def fires(self):
        return self._fires

    def loads(self, format=FireDataFormats.JSON):
        loader = getattr(self, "_from_%s" % (FireDataFormats.get_format_str(format)), None)
        if not loader:
            raise FireDataFormatNotSupported
        self._fires = loader(self._stream(self._input_file, 'r'))
        return self._fires

    def dumps(self, format=FireDataFormats.JSON):
        if self._fires is None:
            raise RuntimeError("Fires not yet loaded")

        if format == FireDataFormats.JSON:
            data = json.dumps(self._fires)
        elif format == FireDataFormats.CSV:
            # TODO: need to k
            # TDOO: implement
            raise NotImplementedError
        else:
            raise FireDataFormatNotSupported

        self._stream(self._output_file, 'w').write(data)
