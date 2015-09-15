"""bluesky.models.fires"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import csv
import json
import sys
import uuid

__all__ = [
    'Fire',
    'InvalidFilterError',
    'FiresManager'
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

class FiresManager(object):

    def __init__(self, fires=[], input_file=None, output_file=None):
        self._meta = {}
        self._input_file = input_file
        self._output_file = output_file
        self.fires = fires

    ## Importing

    def _add_fire(self, fire):
        self._fires = self._fires or {}
        if not self._fires.has_key(fire.id):
            self._fires[fire.id] = (fire)
            self._fire_ids.append(fire.id)
        else:
            # TODO: merge into existing (updateing start/end/size/etc appropriately)
            pass

    ## IO

    # TODO: Remove this method and use bluesky.io.Stream in code below instead
    # (would have a fair amoubnt of unit test updates)
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

    @property
    def meta(self):
        return self._meta

    # @property(self):
    # def meta(self):
    #     return self._meta

    def __getattr__(self, attr):
        """Provides get access to meta data

        Note: __getattr__ is called when the 'attr' isn't defined on self
        """
        return self._meta.get(attr)

    def __setattr__(self, attr, val):
        """Provides set access to meta data

        Note: __setattr__ is always called, whether or not 'attr' is defined
        on self.  So, we have to make sure this is meta data, and call super's
        __setattr__ if not.
        """
        if not attr.startswith('_') and not hasattr(FiresManager, attr):
            self._meta[attr] = val
        super(FiresManager, self).__setattr__(attr, val)

    @fires.setter
    def fires(self, fires_list):
        self._fires = {}
        self._fire_ids = []
        for fire in fires_list:
            self._add_fire(fire)

    def loads(self):
        """Loads json-formatted fire data, creating list of Fire objects and
        storing other fields in self.meta.

        TODO:
         - support already parsed JSON (i.e. dict or array)
        """
        stream = self._stream(self._input_file, 'r')
        data = json.loads(''.join([d for d in stream]))
        if not hasattr(data, 'keys'):
            raise ValueError("Invalid fire data")
        new_fires = [Fire(d) for d in data.pop('fire_information', [])]
        for fire in new_fires:
            self._add_fire(fire)
        self._meta = data

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
        stream = self._stream(self._output_file, 'w')
        fire_json = json.dumps(dict(self._meta, fire_information=self.fires), cls=FireEncoder)
        stream.write(fire_json)
