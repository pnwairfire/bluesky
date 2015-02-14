"""tasks.takedown - fabric tasks for ....
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import csv
import json
import sys
import uuid

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

    SYNONYMS = {
        "date_time": "start"
        # TODO: fill in other synonyms
    }

    def __init__(self, *args, **kwargs):
        super(Fire, self).__init__(*args, **kwargs)

        # keep track of attrs generated during initialization
        self.auto_initialized_attrs = []

        for k,v in self.SYNONYMS.items():
            if self.has_key(k) and not self.has_key(v):
                # TDOO: should we pop 'k':
                #  >  self[v] = self.pop(k)
                self[v] = self[k]
                self.auto_initialized_attrs.append(v)

        # if id isn't specified, create it using other fields
        if not self.get('id'):
            self['id'] = '-'.join([str(e) for e in [
                str(uuid.uuid1())[:8],
                self.get('start'),
                self.get('end')
            ] if e]).replace(' ', '')
            self.auto_initialized_attrs.append('id')

        if not self.get('name'):
            self['name'] = 'Unknown-%s' % (self['id'])
            self.auto_initialized_attrs.append('name')

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]
        raise KeyError(attr)

    def __setattr__(self, attr, val):
        if attr != 'auto_initialized_attrs':
            self[attr] = val
        else:
            super(Fire, self).__setattr__(attr, val)

class FireEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)

class FiresImporter(object):

    def __init__(self, input_file=None, output_file=None):
        self._input_file = input_file
        self._output_file = output_file
        self._fires = {}
        self._fire_ids = [] # to record order fires were added

    ## Importing

    def _add_fire(self, fire):
        self._fires = self._fires or {}
        if not self._fires.has_key(fire.id):
            self._fires[fire.id] = (fire)
            self._fire_ids.append(fire.id)
        else:
            # TODO: merge into existing (updateing start/end/size/etc appropriately)
            pass

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
            self._add_fire(Fire(data))
        elif hasattr(data, 'append'):
            if len(data) > 0:
                new_fires = [Fire(d) for d in data]
                for fire in new_fires:
                    self._add_fire(fire)
        else:
            raise ValueError("Invalid fire json data")

    def _from_csv(self, stream):
        headers = []
        for row in csv.reader(stream):
            if not headers:
                # record headers for this csv data
                #headers = dict([(i, row[i].strip(' ')) for i in xrange(len(row))])
                headers = [e.strip(' ') for e in row]
            else:
                fire = Fire(dict([(headers[i], row[i].strip(' ')) for i in xrange(len(row))]))
                self._cast_numeric_values(fire)
                self._add_fire(fire)

    def _cast_numeric_values(self, fire):
        # TODO: better way to automatically parse numerical values
        for k in fire.keys():
            try:
                # try to parse int
                fire[k] = int(fire[k])
            except ValueError:
                try:
                    # try to parse float
                    fire[k] = float(fire[k])
                except:
                    # leave it as a string
                    pass

    ## Exporting

    def _to_json(self, stream):
        stream.write(json.dumps(self.fires, cls=FireEncoder))

    def _to_csv(self, stream):
        # TDOO: implement
        # TODO: if self._headers is defined, then use it to order the first
        # N columns of the fire data.  (After that will come the data augmented
        # by the BlueSky modules run on the data.  For those columns, maybe just
        # organize them in alphabetical order)

        csvfile = csv.writer(stream, lineterminator='\n')
        csvfile.writerow(self._headers)
        for f in self.fires:
            a = [f.get(h,'') for h in self._headers]
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
        return [self._fires[i] for i in self._fire_ids]

    @fires.setter
    def fires(self, fires_list):
        self._fires = {}
        self._fire_ids = []
        for fire in fires_list:
            self._add_fire(fire)


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

        def _filter(fire, attr):
            if whitelist:
                return hasattr(fire, attr) and getattr(fire, attr) in whitelist
            else:
                return not hasattr(fire, attr) or getattr(fire, attr) not in blacklist
        self.fires = [f for f in self.fires if _filter(f, attr)]

    def dumps(self, format=FireDataFormats.JSON):
        # If not fires have yet been loaded, just return empty array

        dumper = getattr(self, "_to_%s" % (FireDataFormats[format]), None)
        if not dumper:
            raise FireDataFormatNotSupported("Unsupported output format: %s" % (format))
        dumper(self._stream(self._output_file, 'w'))
