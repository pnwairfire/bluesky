"""bluesky.models.fires"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

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

    @property
    def latitude(self):
        # This is if latitude is a true top level key
        if 'latitude' in self:
            return self['latitude']
        # This is if latitude is nested somewhere or needs to be derived
        if not hasattr(self, '_latitude'):
            if self.location and 'latitude' in self.location:
                self._latitude = self.location['latitude']
            elif self.location and 'perimeter' in self.location:
                # TODO: get centroid of perimeter(s); also, can't assume 3-deep nested
                # array (it's 3-deep for MultiPolygon, but not necessarily other shape types)
                # see https://en.wikipedia.org/wiki/Centroid
                self._latitude = self.location['perimeter']['coordinates'][0][0][0][1]
                self._longitude = self.location['perimeter']['coordinates'][0][0][0][0]
            elif self.location and 'shape_file' in self.location:
                raise NotImplementedError("Importing of shape data from file not implemented")
            else:
                raise ValueError("Insufficient location data required for "
                    "determining single lat/lng for fire")
        return self._latitude

    @property
    def longitude(self):
        # This is if longitude is a true top level key
        if 'longitude' in self:
            return self['longitude']
        # This is if longitude is nested somewhere or needs to be derived
        if not hasattr(self, '_longitude'):
            if self.location and 'longitude' in self.location:
                self._longitude = self.location['longitude']
            elif self.location and 'perimeter' in self.location:
                # TODO: get centroid of perimeter(s); also, can'st assume 3-deep nested
                # array (it's 3-deep for MultiPolygon, but not necessarily other shape types)
                # see https://en.wikipedia.org/wiki/Centroid
                self._latitude = self.location['perimeter']['coordinates'][0][0][0][1]
                self._longitude = self.location['perimeter']['coordinates'][0][0][0][0]
            elif self.location and 'shape_file' in self.location:
                raise NotImplementedError("Importing of shape data from file not implemented")
            else:
                raise ValueError("Insufficient location data required for "
                    "determining single lat/lng for fire")
        return self._longitude

    def __getattr__(self, attr):
        if attr in self.keys():
            return self[attr]
        raise KeyError(attr)

    def __setattr__(self, attr, val):
        if not attr.startswith('_') and not hasattr(Fire, attr):
            self[attr] = val
        else:
            super(Fire, self).__setattr__(attr, val)

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

    def add_fire(self, fire):
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
            self.add_fire(Fire(fire))

    @property
    def modules(self):
        return self._module_names

    @property
    def run_id(self):
        if not self._meta.get('run_id'):
            self._meta['run_id'] = str(uuid.uuid1())
        return self._meta['run_id']

    @modules.setter
    def modules(self, module_names):
        self._module_names = module_names
        self._modules = []
        for m in module_names:
            try:
                self._modules.append(importlib.import_module('bluesky.modules.%s' % (m)))
            except ImportError, e:
                if e.message == 'No module named {}'.format(m):
                    raise BlueSkyImportError("Invalid module '{}'".format(m))
                else:
                    logging.debug(traceback.format_exc())
                    raise BlueSkyImportError("Error importing module {}".format(m))

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
        v = {
            'module': module_name,
            'version': version,
        }
        if data:
            v.update(data)

        if not self.processing or self.processing[-1].keys() != ['module_name']:
            self.processing = self.processing or []
            self.processing.append(v)
        else:
            self.processing[-1].update(v)

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

    def run(self): #, module_names):
        failed = False
        for i in range(len(self._modules)):
            # if one of the modules already failed, then the only thing
            # we'll run from here on is the export module
            if failed and 'export' != self._module_names[i]:
                continue

            try:
                # initialize processing recotd
                self.processing = self.processing or []
                self.processing.append({
                    "module_name": self._module_names[i]
                })

                # 'run' modifies fires in place
                self._modules[i].run(self)
            except Exception, e:
                failed = True
                # when there's an error running modules, don't bail; continue
                # iterating through requested modules, executing only exports
                # and then raise BlueSkyModuleError, below, so that the calling
                # code can decide what to do (which, in the case of bsp and
                # bsp-web, is to dump the data as is)
                logging.error(e)
                tb = traceback.format_exc()
                logging.debug(tb)
                self.error = {
                    "module": self._module_names[i],
                    "message": str(e),
                    "traceback": str(tb)
                }

        if failed:
            # If there was a failure
            raise BlueSkyModuleError

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
        # Don't include 'modules' in the output. The modules to be run may have
        # been specified on the command line or in the input json. Either way,
        # 'processing' contains a record of what modules were run (though it may
        # be fewer modules than what were requested, which would be the case
        # if there was a failure).  We don't want to include 'modules' in the
        # output because that breaks the ability to pipe the results into
        # another run of bsp.
        # TODO: keep track of whether modules were specified in the input
        # json or on the command line, and add them to the output if they
        # were in the input
        return dict(self._meta, fire_information=self.fires)

    def dumps(self, output_stream=None, output_file=None):
        if output_stream and output_file:
            raise RuntimeError("Don't specify both output_stream and output_file")
        if not output_stream:
            output_stream = self._stream(output_file, 'w')
        fire_json = json.dumps(self.dump(), cls=FireEncoder)
        output_stream.write(fire_json)
