"""bluesky.loaders

The loader packages and classes should be organized and named such that, given
the source name (e.g. 'Smartfire2'), format (e.g. 'CSV'), and 'type' (e.g.
'file'), bluesky.modules.load can dynamically import the module with:

    >>> loader_module importlib.import_module(
        'bluesky.loaders.<source_name_to_lower_case>.<format_to_lower_case>')'

and then get the loading class with:

    >>> getattr(loader_module, '<source_type_capitalized>Loader')

For example, the smartfire csv file loader is in module
bluesky.loaders.smartfire.csv and is called FileLoader
"""

import datetime
import logging
import os

from pyairfire.io import CSV2JSON

from bluesky import datetimeutils
from bluesky.exceptions import BlueSkyConfigurationError

__author__ = "Joel Dubowy"

class BaseFileLoader(object):

    def __init__(self, **config):
        self._filename = config.get('file')
        if not self._filename:
            raise BlueSkyConfigurationError("Fires file to load not specified")
        if not os.path.isfile(self._filename):
            raise BlueSkyConfigurationError("Fires file to load {} does not "
                "exist".format(self._filename))

        self._events_filename = None
        if config.get('events_file'):
            self._events_filename = config['events_file']
            if not os.path.isfile(self._events_filename):
                raise BlueSkyConfigurationError("Fire events file to load {} "
                    "does not exist".format(self._events_filename))

    ##
    ## File IO
    ##

    def _load_csv_file(self, filename):
        csv_loader = CSV2JSON(input_file=filename)
        return csv_loader._load()

    # TODO: provide other file reading functionality as needed
