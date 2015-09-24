"""bluesky.models.fires"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import csv
import importlib
import json
import logging
import sys
import traceback
import uuid

from bluesky import datautils, configuration
from bluesky.exceptions import (
    BlueSkyImportError, BlueSkyModuleError, InvalidFilterError
)

__all__ = [
    'Fire',
    'FiresManager'
]


class Fire(dict):

    def __init__(self, *args, **kwargs):
        super(Fire, self).__init__(*args, **kwargs)

        # if id isn't specified, set to new guid
        if not self.get('id'):
            self['id'] = str(uuid.uuid1())[:8]

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]
        raise KeyError(attr)

    def __setattr__(self, attr, val):
        self[attr] = val

class FireEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()

        return json.JSONEncoder.default(self, obj)

class FiresManager(object):

    def __init__(self):
        self._meta = {}
        self.modules = []
        self.fires = []

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

    ##
    ## 'Public' Methods
    ##

    @property
    def fires(self):
        return [self._fires[i] for i in self._fire_ids]

    @fires.setter
    def fires(self, fires_list):
        self._fires = {}
        self._fire_ids = []
        for fire in fires_list:
            self._add_fire(Fire(fire))

    @property
    def modules(self):
        return self._module_names

    @modules.setter
    def modules(self, module_names):
        self._module_names = module_names
        self._modules = []
        for m in module_names:
            try:
                self._modules.append(importlib.import_module('bluesky.modules.%s' % (m)))
            except ImportError, e:
                raise BlueSkyImportError("Invalid module '{}'".format(m))

    @property
    def meta(self):
        return self._meta

    def get_config_value(self, *keys, **kwargs):
        return configuration.get_config_value(self.config, *keys, **kwargs)

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

    def processed(self, module_name, version, **data):
        # TODO: determine module from call stack rather than require name
        # to be passed in.  Also get version from module's __version__
        self.processing = self.processing or []
        v = {
            'module': module_name,
            'version': version,
        }
        if data:
            v.update(data)
        self.processing.append(v)

    def summarize(self, **data):
        self.summary = self.summary or {}
        self.summary = datautils.deepmerge(self.summary, data)

    ## Loading data

    def load(self, input_dict):
        if not hasattr(input_dict, 'keys'):
            raise ValueError("Invalid fire data")

        # wipe out existing list of modules, if any
        self.modules = input_dict.pop('modules', [])

        # wipe out existing fires, if any
        self.fires = input_dict.pop('fire_information', [])

        self._meta = input_dict

    def loads(self, input_stream=None, input_file=None):
        """Loads json-formatted fire data, creating list of Fire objects and
        storing other fields in self.meta.
        """
        if input_stream and input_file:
            raise RuntimeError("Don't specify both input_stream and input_file")
        if not input_stream:
            input_stream = self._stream(input_file, 'r')
        data = json.loads(''.join([d for d in input_stream]))
        return self.load(data)

    def run(self):
        try:
            for module in self._modules:
                # TODO: catch any exception raised by a module and dumps
                # whatever is the current state of fires (or state of fires prior
                # to calling hte module) ?
                # 'run' modifies fires in place
                module.run(self)
        except Exception, e:
            # when there's an error running modules, don't bail; raise
            # BlueSkyModuleError so that the calling code can decide what to do
            # (which, in the case of bsp and bsp-web, is to dump the data as is)
            logging.error(e)
            tb = traceback.format_exc()
            logging.debug(tb)
            fires_manager.error = {
                "message": str(e),
                "traceback": str(tb)
            }
            raise BlueSkyModuleError(e)

    ## Filtering data

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

    ## Dumping data

    def dump(self):
        return dict(self._meta, fire_information=self.fires, modules=self.modules)

    def dumps(self, output_stream=None, output_file=None):
        if output_stream and output_file:
            raise RuntimeError("Don't specify both output_stream and output_file")
        if not output_stream:
            output_stream = self._stream(output_file, 'w')
        fire_json = json.dumps(self.dump(), cls=FireEncoder)
        output_stream.write(fire_json)
