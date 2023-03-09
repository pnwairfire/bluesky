"""bluesky.config"""

import copy
import threading

import afconfig

# make sure importing AVAILABLE_MODULES doesn't result in
# circular importsx
from bluesky import datetimeutils
from bluesky.exceptions import (
    BlueSkyDatetimeValueError
)
from bluesky.modules import AVAILABLE_MODULES
from .defaults import DEFAULTS, to_lowercase_keys

__all__ = [
    "Config",
    "DEFAULTS"
]

# we'll make config data thread safe by storing in thread local,
# which must be defined once, in main thread.
thread_local_data = threading.local()

class Config(object):

    # This is a Singleton, to facilitate making this module thread safe
    # (e.g. when using threads to execute parallel runs with different
    # configurations)

    def __new__(cls, *args, **kwargs):
        if not hasattr(thread_local_data, 'config_manager'):
            thread_local_data.config_manager = object.__new__(cls)
        return thread_local_data.config_manager

    def __init__(self):
        # __init__ will be called each time __new__ is called. So, we need to
        # keep track of initialization to abort subsequent reinitialization
        if not hasattr(self, '_initialized'):
            self._data = thread_local_data
            self.reset()
            self._initialized = True

    ##
    ## Main interface
    ##

    def reset(self):
        self._data._RUN_ID = None
        self._data._TODAY = None
        self._data._RAW_CONFIG = copy.deepcopy(DEFAULTS)
        self._data._CONFIG = copy.deepcopy(self._data._RAW_CONFIG)
        self._data._IM_CONFIG = afconfig.ImmutableConfigDict(self._data._CONFIG)

        return self

    def merge(self, config_dict):
        if config_dict:
            config_dict = to_lowercase_keys(config_dict)
            self._data._RAW_CONFIG = afconfig.merge_configs(
                self._data._RAW_CONFIG, config_dict)
            self._data._CONFIG = afconfig.merge_configs(self._data._CONFIG,
                self.replace_config_wildcards(copy.deepcopy(config_dict)))
            self._data._IM_CONFIG = afconfig.ImmutableConfigDict(self._data._CONFIG)

        return self

    def set(self, config_dict, *keys):
        config_dict = to_lowercase_keys(config_dict)
        if keys:
            keys = [k.lower() for k in keys]
            afconfig.set_config_value(self._data._RAW_CONFIG,
                copy.deepcopy(config_dict), *keys)
            afconfig.set_config_value(self._data._CONFIG,
                self.replace_config_wildcards(copy.deepcopy(config_dict)),
                *keys)
            self._data._IM_CONFIG = afconfig.ImmutableConfigDict(self._data._CONFIG)

        else:
            self._data._RAW_CONFIG = copy.deepcopy(DEFAULTS)
            self._data._CONFIG = copy.deepcopy(self._data._RAW_CONFIG)
            self.merge(config_dict)

        return self

    def set_today(self, today):
        if today and self._data._TODAY != today:
            self._data._TODAY = today
            self.set(self._data._RAW_CONFIG)

    def set_run_id(self, run_id):
        if run_id and self._data._RUN_ID != run_id:
            self._data._RUN_ID = run_id
            self.set(self._data._RAW_CONFIG)

    def get(self, *keys, **kwargs):
        if 'default' in kwargs:
            raise DeprecationWarning("config defaults are specified in "
                "bluesky.config.defaults module")

        if keys:
            keys = [k.lower() for k in keys]
            # default behavior is to fail if key isn't in user's config
            # or in default config
            return afconfig.get_config_value(self._data._IM_CONFIG, *keys,
                fail_on_missing_key=not kwargs.get('allow_missing'))

        else:
            return self._data._IM_CONFIG

    def replace_config_wildcards(self, val):
        if isinstance(val, dict):
            for k in val:
                val[k] = self.replace_config_wildcards(val[k])
        elif isinstance(val, list):
            val = [self.replace_config_wildcards(v) for v in val]
        elif hasattr(val, 'lower'):  # i.e. it's a string
            if val:
                # first, fill in any datetime control codes or wildcards
                val = datetimeutils.fill_in_datetime_strings(val,
                    today=self._data._TODAY)

                # then, see if the resulting string purely represents a datetime
                try:
                    val = datetimeutils.to_datetime(val, limit_range=True)
                except BlueSkyDatetimeValueError:
                    pass

                if hasattr(val, 'capitalize'):
                    # This gets rid of datetime parsing busters embedded
                    # in strings to prevent conversion to datetime object
                    val = val.replace('{datetime-parse-buster}', '')

                    if self._data._RUN_ID:
                        val = val.replace('{run_id}', self._data._RUN_ID)

                # TODO: any other replacements?

        return val
