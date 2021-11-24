"""bluesky.models.fires"""

__author__ = "Joel Dubowy"

import datetime
import importlib
import itertools
import io
import json
import logging
import sys
import traceback
import urllib.request
import uuid
import gzip
from collections import OrderedDict

import requests
from pyairfire import process

from bluesky import datautils, datetimeutils, __version__
from bluesky.config import Config
from bluesky.exceptions import (
    BlueSkyImportError, BlueSkyModuleError
)
from bluesky.filtermerge.filter import FireActivityFilter
from bluesky.filtermerge.merge import FiresMerger
from bluesky.statuslogging import StatusLogger

from .activity import ActiveArea, ActivityCollection

__all__ = [
    'Fire',
    'FiresManager'
]


##
## Fire
##


class Fire(dict):

    DEFAULT_TYPE = 'wildfire'
    DEFAULT_FUEL_TYPE = 'natural'

    def __init__(self, *args, **kwargs):
        super(Fire, self).__init__(*args, **kwargs)

        # private id used to identify fire from possibly multiple fires with
        # the same public 'id' (e.g. in FiresManager's failure handler)
        self._private_id = str(uuid.uuid4())

        # if id isn't specified, set to new guid
        if not self.get('id'):
            self['id'] = str(uuid.uuid4())[:8]

        if not self.get('type'):
            self['type'] = self.DEFAULT_TYPE
        # TODO: figure out how to not have to explicitly call _validate_type here
        else:
            self['type'] = self._validate_type(self['type'])

        if not self.get('fuel_type'):
            self['fuel_type'] = self.DEFAULT_FUEL_TYPE
        # TODO: figure out how to not have to explicitly call _validate_fuel_type here
        else:
            self['fuel_type'] = self._validate_fuel_type(self['fuel_type'])

        # convert each active area dict into an ActiveArea Object
        for i in range(len(self.get('activity', []))):
            self['activity'][i] = ActivityCollection(self['activity'][i])

    ## Properties

    # @property
    # def raw_dict(self):
    #     return {k: self[k] for k in self}

    @property
    def active_areas(self):
        """Returns flat list of fire active areas, from across all activity
        collections.

        We could memoize this method, but would need to invalidate
        when adding/removing collections or active areas, or when
        modifying points or perimeters.
        """
        return list(itertools.chain.from_iterable(
            [ac.active_areas for ac in self.get('activity', [])]
        ))

    @property
    def locations(self):
        """Returns flat list of locations from across all active areas

        Use in summarizing code.
        """
        return list(itertools.chain.from_iterable(
            [aa.locations for aa in self.active_areas]))


    @property
    def start(self):
        """Returns start of initial activity window

        Doesn't memoize, in case activity windows are added/removed/modified
        """
        # consider only activie areas with start times
        active_areas = [a for a in self.active_areas if a.get('start')]
        if active_areas:
            active_areas = sorted(active_areas, key=lambda a: a['start'])
            # record utc offset of initial active area, in case
            # start_utc is being called
            self.__utc_offset = active_areas[0].get('utc_offset')
            return datetimeutils.parse_datetime(active_areas[0]['start'], 'start')

    @property
    def start_utc(self):
        return self._to_utc(self.start)

    @property
    def end(self):
        """Returns end of final activity window

        Doesn't memoize, in case activity windows are added/removed/modified

        TODO: take into account possibility of activity objects having different
          utc offsets.  (It's an extreme edge case where one start/end string
          is gt/lt another when utc offset is ignored but not when utc offset
          is considered, so this isn't a high priority)
        """
        # consider only activie areas with end times
        active_areas = [a for a in self.active_areas if a.get('end')]
        if active_areas:
            active_areas = sorted(active_areas, key=lambda a: a['end'])
            # record utc offset of initial active area, in case
            # start_utc is being called
            self.__utc_offset = active_areas[-1].get('utc_offset')
            return datetimeutils.parse_datetime(active_areas[-1]['end'], 'end')

    @property
    def end_utc(self):
        return self._to_utc(self.end)

    def _to_utc(self, dt):
        if dt:
            if self.__utc_offset:
                dt = dt - datetime.timedelta(
                    hours=datetimeutils.parse_utc_offset(self.__utc_offset))
            # else, assume zero offset
            return dt

   ## Validation

    VALID_TYPES = {
        'wildfire': 'wildfire',
        'wf': 'wildfire',
        'rx':'rx',
        'unknown': 'unknown'
    }
    INVALID_TYPE_MSG = "Invalid fire 'type': {}"

    def _validate_type(self, val):
        val = val.lower()
        if val not in self.VALID_TYPES:
            raise ValueError(self.INVALID_TYPE_MSG.format(val))
        return self.VALID_TYPES[val]

    @property
    def is_wildfire(self):
        return self.type == 'wildfire'

    VALID_FUEL_TYPES = ('natural', 'activity', 'piles')
    INVALID_FUEL_TYPE_MSG = "Invalid fire 'fuel_type': {}"

    def _validate_fuel_type(self, val):
        val = val.lower()
        if val not in self.VALID_FUEL_TYPES:
            raise ValueError(self.INVALID_FUEL_TYPE_MSG.format(val))
        return val

    ## Getters and Setters

    def __setitem__(self, attr, val):
        k = '_validate_{}'.format(attr)
        if hasattr(self, k):
            val = getattr(self, k)(val)
        super(Fire, self).__setitem__(attr, val)

    def __getattr__(self, attr):
        if attr in list(self.keys()):
            return self[attr]
        raise AttributeError(attr)

    def __setattr__(self, attr, val):
        if not attr.startswith('_') and not hasattr(Fire, attr):
            self[attr] = val
        else:
            super(Fire, self).__setattr__(attr, val)


class FireEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()

        return json.JSONEncoder.default(self, obj)


##
## FireManager
##

class FiresManager(object):

    def __init__(self):
        self._meta = {}
        # configuration no longer initialized here
        self.modules = []
        self.fires = [] # this intitializes self._fires and self._num_fires
        self._num_fires = 0
        # call setters for today and run_id, to trigger setting in Config()
        self.today = datetimeutils.today_utc()
        self.run_id = str(uuid.uuid4())

    ##
    ## Importing
    ##

    def add_fires(self, fires):
        for fire in fires:
            # cast to Fire, in case it isn't already
            # TODO: should add_fire do the casting?
            self.add_fire(Fire(fire))

    def add_fire(self, fire):
        self._fires = self._fires or OrderedDict()
        if fire.id not in self._fires:
            self._fires[fire.id] = []
        self._fires[fire.id].append(fire)
        self._num_fires += 1


    def remove_fire(self, fire):
        # TODO: raise exception if fire doesn't exist ?
        if fire.id in self._fires:
            _n = len(self._fires[fire.id])
            self._fires[fire.id] = [f for f in self._fires[fire.id]
                if f._private_id != fire._private_id]
            self._num_fires -= (_n - len(self._fires[fire.id]))
            if len(self._fires[fire.id]) == 0:
                # that was last fire with that id
                self._fires.pop(fire.id)

    ##
    ## Merging Fires
    ##

    def merge_fires(self):
        """Merges fires that have the same id.
        """
        with FiresMerger(self, Fire) as m:
            m.merge()

    ## IO

    # TODO: Remove this method and use bluesky.io.Stream in code below instead
    # (would have a fair amoubnt of unit test updates)
    def _stream(self, file_name, flag, compress=False): #, do_strip_newlines):
        if file_name:
            file_name = datetimeutils.fill_in_datetime_strings(
                file_name, today=self.today)
            file_name = file_name.replace('{run_id}', self.run_id)
            if  file_name.startswith('http'):
                logging.debug("Loading input over http: %s", file_name)
                return io.BytesIO(urllib.request.urlopen(file_name).read())
            else:
                action = "Loading" if (not flag or flag.startswith('r')) else "Writing to"
                logging.debug("%s local file: %s", action, file_name)
                return open(file_name, flag)
        else:
            if flag.startswith('r'):
                return sys.stdin
            else:
                return sys.stdout.buffer if compress else sys.stdout

    ##
    ## Fire Related Properties
    ##

    def _get_fire(self, fire):
        fires_with_id = self._fires.get(fire.id)
        if fires_with_id:
            fires_with_p_id = [f for f in fires_with_id
                if f._private_id == fire._private_id]
            if fires_with_p_id:
                # will be len == 1
                return fires_with_p_id[0]

    @property
    def fires(self):
        return [fire_obj for fire_list in self._fires.values()
            for fire_obj in fire_list]

    @property
    def num_fires(self):
        return self._num_fires

    @property
    def locations(self):
        return list(itertools.chain.from_iterable(
            [f.locations for f in self.fires]))

    @property
    def num_locations(self):
        return sum([len(f.locations) for f in self.fires])

    @fires.setter
    def fires(self, fires_list):
        self._num_fires = 0
        self._fires = OrderedDict()
        for fire in fires_list:
            self.add_fire(Fire(fire))

    ##
    ## Special Meta Attributes
    ##

    ## today

    @property
    def today(self):
        return self._today

    @today.setter
    def today(self, today):
        today = datetimeutils.fill_in_datetime_strings(today)
        today = datetimeutils.to_datetime(today)
        self._today = today
        Config().set_today(self._today)

    ## run_id

    @property
    def run_id(self):
        return self._run_id

    @run_id.setter
    def run_id(self, run_id):
        logging.debug('filling in run_id wildcards')
        self._run_id = datetimeutils.fill_in_datetime_strings(
            run_id, today=self.today)

        Config().set_run_id(self._run_id)

    ## modules

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

            except ImportError as e:
                if str(e) == 'No module named {}'.format(m):
                    raise BlueSkyImportError("Invalid module '{}'".format(m))
                else:
                    logging.debug(traceback.format_exc())
                    raise BlueSkyImportError("Error importing module {}".format(m))

    @property
    def meta(self):
        return self._meta

    def record_error(self, msg):
        self.meta['errors'] = self._meta.get('errors') or []
        self.meta['errors'].append(msg)

    ##
    ## Configuration
    ##

    # All these methods delegate to config.Config

    @property
    def config(self):
        raise DeprecationWarning(
            "Get config with bluesky.config.Config().get")

    @config.setter
    def config(self, config):
        raise DeprecationWarning(
            "Set config with bluesky.config.Config().set")

    def get_config_value(cls, *keys, **kwargs):
        raise DeprecationWarning(
            "Get config values with bluesky.config.Config().get")

    ##
    ## Helper properties
    ##

    @property
    def earliest_start(self):
        start_times = [s for s in [f.start_utc for f in self.fires] if s]
        if start_times:
            return sorted(start_times)[0]
        # TODO: else try to determine from "met", if defined (?)

    @property
    def latest_end(self):
        end_times = [e for e in [f.end_utc for f in self.fires] if e]
        if end_times:
            return sorted(end_times)[-1]
        # TODO: else try to determine from "met", if defined (?)

    @property
    def counts(self):
        counts = {
            'fires': self.num_fires,
            'locations': self.num_locations
        }
        if self.skip_failed_fires:
            counts['failed_fires'] = len(self.failed_fires or [])
        logging.summary("Fire counts: %s", counts)
        return counts


    ##
    ## Meta Properties
    ##


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

    ##
    ## Running Modules
    ##

    def processed(self, module_name, version, **data):
        # TODO: determine module from call stack rather than require name
        # to be passed in.  Also get version from module's __version__
        v = {
            'module': module_name,
            'version': version,
        }
        if data:
            v.update(data)

        # TDOO: checking that
        #     > self.processing[-1].keys() != ['module_name']
        #   seems to be a bug; should it instead be checking that
        #     > self.processing[-1]['module'] != module_name
        #   (though this would be sketchy, since a module may very well have
        #    been run twice in a row)....maybe we should always
        #   append a new record
        if not self.processing or list(self.processing[-1].keys()) != ['module_name']:
            self.processing = self.processing or []
            self.processing.append(v)
        else:
            self.processing[-1].update(v)

    def summarize(self, **data):
        self.summary = self.summary or {}
        self.summary = datautils.deepmerge(self.summary, data)

    def log_status(self, status, step, action, **extra_fields):
        if not getattr(self, '_status_logger'):
            # init_time will be converted to string if it's datetime.date[time]
            init_time = (
                Config().get('dispersion', 'start', allow_missing=True)
                or self.today)
            sl_config = Config().get('statuslogging')
            setattr(self, '_status_logger', StatusLogger(init_time, **sl_config))
        self._status_logger.log(status, step, action, **extra_fields)

    def run(self): #, module_names):
        self.log_status('Good', 'Main', 'Start')
        self.runtime = self.runtime or {"modules": []}
        failed = False

        logging.summary("Modules to be run: %s", ', '.join(self._module_names))

        with process.RunTimeRecorder(self.runtime):
            for i in range(len(self._modules)):
                # if one of the modules already failed, then the only thing
                # we'll run from here on is the export module
                if failed and 'export' != self._module_names[i]:
                    continue

                try:
                    self.runtime['modules'].append({
                        "module_name": self._module_names[i]
                    })
                    with process.RunTimeRecorder(self.runtime['modules'][-1]):
                        # initialize processing recotd
                        self.processing = self.processing or []
                        self.processing.append({
                            "module_name": self._module_names[i]
                        })

                        # 'run' modifies fires in place
                        self.log_status('Good', self._module_names[i], 'Start')
                        logging.summary("Running module %s", self._module_names[i])
                        self._modules[i].run(self)
                        self.log_status('Good', self._module_names[i], 'Finish')
                except Exception as e:
                    failed = True
                    # when there's an error running modules, don't bail; continue
                    # iterating through requested modules, executing only exports
                    # and then raise BlueSkyModuleError, below, so that the calling
                    # code can decide what to do (which, in the case of bsp and
                    # bsp-web, is to dump the data as is)
                    logging.error(str(e))
                    tb = traceback.format_exc()
                    logging.debug(tb)
                    self.error = {
                        "module": self._module_names[i],
                        "message": str(e),
                        "traceback": str(tb)
                    }
                    self.log_status('Failure', self._module_names[i], 'Die')

        if failed:
            self.log_status('Failure', 'Main', 'Die')
            # If there was a failure
            raise BlueSkyModuleError

        self.log_status('Good', 'Main', 'Finish', runtime=self.runtime)

    ## Filtering Fires

    def filter_fires(self):
        with FireActivityFilter(self, Fire) as ff:
            ff.filter()

    ## Failures

    @property
    def fire_failure_handler(self):
        """Context manager that moves failed fires

        The reason for defining a method that returns a context manager class,
        is that the closure allows the call to not have to pass in the
        fires_manager object itself.

            for fire in fires_manager.fires:
                with fires_manager.fire_failure_handler(fire):
                    ....

        as opposed to:

            for fire in fires_manager.fires:
                with fires_manager.fire_failure_handler(fires_manager, fire):
                    ....
        """
        fires_manager = self
        class klass(object):
            def __init__(self, fire):
                self._fire = fire

            def __enter__(self):
                pass

            def __exit__(self, e_type, value, tb):
                if e_type:
                    # there was a failure; first see if fire is in fact
                    # managed by fires_manager
                    f = fires_manager._get_fire(self._fire)
                    if f:
                        # Add error infromation to fire object.
                        # Note that error information will also be added to
                        # top level if skip_failed_fires == False
                        f.error = {
                            "type": value.__class__.__name__,
                            "message": str(value),
                            "traceback": str(traceback.format_tb(tb))
                        }
                        if fires_manager.skip_failed_fires:
                            logging.warning(str(value))
                            logging.warning(str(traceback.format_tb(tb)))
                            # move fire to failed list, excluding it from
                            # future processing
                            if fires_manager.failed_fires is None:
                                fires_manager.failed_fires  = []
                            fires_manager.failed_fires.append(f)
                            # remove fire from good fires list
                            fires_manager.remove_fire(f)
                            return True
                        # else, let exception, if any, be raised
                    else:
                        # fire was not one of fires_manager's
                        # TODO: don't raise exception if configured not to
                        #  (maybe also controlled by
                        #   fires_manager.skip_failed_fires?)
                        raise RuntimeError("Fire {} ({}) not managed by "
                            "fires_manager".format(self._fire.id,
                            self._fire._private_id))

        return klass

    @property
    def skip_failed_fires(self):
        return not not Config().get('skip_failed_fires')

    ## Loading data

    def load(self, input_dict, append_fires=False):
        if not hasattr(input_dict, 'keys'):
            raise ValueError("Invalid fire data")

        # wipe out existing list of modules, if any
        self.modules = input_dict.pop('modules', [])

        # wipe out existing fires, if any, if append_fires==False
        new_fires = (input_dict.pop('fires', [])
            or input_dict.pop('fire_information', []))
        self.fires = self.fires + new_fires if append_fires else new_fires

        # pop config, but don't set until after today has been set
        if 'config' in input_dict:
            raise DeprecationWarning("Don't specify 'config' in input data")

        if 'run_config' in input_dict:
            logging.info("Ignoring previous output config in the input data")
            input_dict.pop('run_config')

        today = input_dict.pop('today', None)
        if today:
            self.today = today

        run_id = input_dict.pop('run_id', None)
        if run_id:
            self.run_id = run_id

        self._meta.update(input_dict)

    def loads(self, input_stream=None, input_file=None, append_fires=False):
        """Loads json-formatted fire data, creating list of Fire objects and
        storing other fields in self.meta.
        """
        if input_stream and input_file:
            raise RuntimeError("Don't specify both input_stream and input_file")

        if not input_stream:
            input_stream = self._stream(input_file, 'rb')
        input_stream = b''.join([
            d.encode() if hasattr(d, 'encode') else d for d in input_stream])

        try:
            input_stream = gzip.decompress(input_stream)
            logging.info("Decompressed input")
        except Exception as e:
            logging.debug("Failed to gzip.decompress: %s", e)
            logging.info("input not gzip'd")

        input_stream = input_stream.decode()

        try:
            data = json.loads(input_stream)
        except json.decoder.JSONDecodeError as e:
            raise ValueError(f"Invalid json: {str(e)}")

        return self.load(data, append_fires=append_fires)

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

        return dict(self._meta, fires=self.fires, today=self.today,
            run_id=self.run_id, counts=self.counts, bluesky_version=__version__,
            run_config=Config().get())

    def dumps(self, output_stream=None, output_file=None, indent=None,
            compress=False):
        if output_stream and output_file:
            raise RuntimeError("Don't specify both output_stream and output_file")

        # ensure that output file name ends with .gz if compressing?
        if output_file and compress and not output_file.endswith('.gz'):
            output_file += '.gz'

        if not output_stream:
            flag = 'wb' if compress else 'w'
            output_stream = self._stream(output_file, flag, compress=compress)
        fire_json = json.dumps(self.dump(), sort_keys=True, cls=FireEncoder,
            indent=indent)
        if compress:
            fire_json = gzip.compress(fire_json.encode())

        output_stream.write(fire_json)
