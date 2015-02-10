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
    'Fire',
    'InvalidFilterError',
    'FiresImporter'
]

class FireDataFormatNotSupported(ValueError):
    pass

class InvalidFilterError(ValueError):
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
            if hasattr(attr, 'lower'):
                attr = attr.lower()

            if attr == 'formats':
                return cls._formats.keys()
            if attr == 'format_ids':
                return cls._r_formats.keys()

            if cls._formats.has_key(attr):
                return cls._formats[attr]
            if cls._r_formats.has_key(attr):
                return cls._r_formats[attr]

            raise FireDataFormatNotSupported(
                "%s is not a valid fire data format" % (attr))
        __getitem__ = __getattr__

    # @property
    # @classmethod
    # def formats(cls):
    #     return cls._formats.keys()

    # @property
    # @classmethod
    # def format_ids(cls):
    #     return cls._r_formats.keys()

class Fire(dict):

    def __init__(self, *args, **kwargs):
        super(Fire, self).__init__(*args, **kwargs)

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]
        raise KeyError(attr)

class FiresImporter(object):

    def __init__(self, input_file=None, output_file=None):
        self._input_file = input_file
        self._output_file = output_file
        self._fires = None
        self._headers = None

    ## Importing

    def _from_json(self, stream):
        """Returns array of Fire objects loaded from json

        Always returns an array, even if json input represents a single fire
        object

        Args:
         - stream -- file object or other iterable object

        TODO:
         - support already parsed JSON (i.e. dict or array)
        """
        self._fires = self._fires or []
        data = json.loads(''.join([d for d in stream]))
        if hasattr(data, 'keys'):
            self._fires = [Fire(data)]
        elif hasattr(data, 'append'):
            self._fires = [Fire(d) for d in data]
        else:
            raise ValueError("Invalid fire json data")

    def _from_csv(self, stream):
        self._fires = self._fires or []
        self._headers = self._headers or []
        headers = []
        for row in csv.reader(stream):
            if not headers:
                # record headers for this csv data
                #headers = dict([(i, row[i].strip(' ')) for i in xrange(len(row))])
                headers = [e.strip(' ') for e in row]
                # add any new headers to those recorded from previously loaded data
                self._headers.extend(set(headers) - set(self._headers))
            else:
                self._fires.append(Fire(dict([(headers[i], row[i].strip(' ')) for i in xrange(len(row))])))
                # TODO: better way to automatically parse numerical values
                for k in self._fires[-1].keys():
                    try:
                        # try to parse int
                        self._fires[-1][k] = int(self._fires[-1][k])
                    except ValueError:
                        try:
                            # try to parse float
                            self._fires[-1][k] = float(self._fires[-1][k])
                        except:
                            # leave it as a string
                            pass

    ## Exporting

    def _to_json(self, stream):
        stream.write(json.dumps(self._fires))

    def _to_csv(self, stream):
        # TDOO: implement
        # TODO: if self._headers is defined, then use it to order the first
        # N columns of the fire data.  (After that will come the data augmented
        # by the BlueSky modules run on the data.  For those columns, maybe just
        # organize them in alphabetical order)

        # Note: assumes each fire has the same set of keys
        # TODO: assert that this is true, and fail if it isn't?
        headers = self._headers or []
        if self._fires: # i.e. defined and has at least one fire
            headers.extend(set(self._fires[0].keys()) - set(headers))

        csvfile = csv.writer(stream)
        csvfile.writerow(headers)
        for f in self._fires:
            a = [f.get(h,'') for h in headers]
            csvfile.writerow(a)

    ## IO

    # TODO: implement this as a context-managing class, with __enter__ and
    # __exit__ methods
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
        loader = getattr(self, "_from_%s" % (FireDataFormats[format]), None)
        if not loader:
            raise FireDataFormatNotSupported("Unsupported format: %s" % (format))
        loader(self._stream(self._input_file, 'r'))

    def filter(self, attr, **kwargs):
        whitelist = kwargs.get('whitelist')
        blacklist = kwargs.get('blacklist')
        if (not whitelist and not blacklist) or (whitelist and blacklist):
            raise InvalidFilterError("Specify whitelist or blacklist - not both")

        _filter = (lambda e: e in whitelist) if whitelist else (lambda e: e not in blacklist)
        self._fires = [f for f in self._fires if _filter(getattr(f, attr))]

    def dumps(self, format=FireDataFormats.JSON):
        if self._fires is None:
            raise RuntimeError("Fires not yet loaded")

        dumper = getattr(self, "_to_%s" % (FireDataFormats[format]), None)
        if not dumper:
            raise FireDataFormatNotSupported("Unsupported output format: %s" % (format))
        dumper(self._stream(self._output_file, 'w'))
