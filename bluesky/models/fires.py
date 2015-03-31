"""tasks.takedown - fabric tasks for ....
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import csv
import json
import sys
import uuid

__all__ = [
    'Fire',
    'InvalidFilterError',
    'FiresImporter'
]

class InvalidFilterError(ValueError):
    pass

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

    ## Exporting

    def _to_json(self, stream):
        stream.write(json.dumps(self.fires, cls=FireEncoder))

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

    def loads(self):
        self._from_json(self._stream(self._input_file, 'r'))

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

    def dumps(self):
        # If not fires have yet been loaded, just return empty array

        self._to_json(self._stream(self._output_file, 'w'))
