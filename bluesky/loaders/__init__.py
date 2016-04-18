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
import os

from pyairfire.datetime.parsing import parse as parse_dt
from pyairfire.io import CSV2JSON

from bluesky.exceptions import BlueSkyConfigurationError

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

class BaseLoader(object):

    def __init__(self, **config):
        if config.get('date_time'):
            if not isinstance(config['date_time'], datetime.date):
                self._date_time = parse_dt(config['date_time'])
            else:
                self._date_time = config['date_time']
        else:
            # default to current date (local time)
            self._date_time = datetime.date.today()


class BaseFileLoader(BaseLoader):

    def __init__(self, **config):
        super(BaseFileLoader, self).__init__(**config)
        self._filename = self._get_filename(config.get('file'))

        self._events_filename = None
        if config.get('events_file'):
            self._events_filename = self._get_filename(config['events_file'])

    ##
    ## General File Utilities
    ##

    def _get_filename(self, filename):
        if not filename:
            raise BlueSkyConfigurationError('Specify a file to load')

        # if file does exist with, try filling in datetime codes
        if not os.path.isfile(filename):
            filename = self._date_time.strftime(filename)

            # if it still doesn't exist, raise exception
            if not os.path.isfile(filename):
                raise BlueSkyConfigurationError('File {} does not exist'.format(
                    filename))

        return filename

    ##
    ## File IO
    ##

    def _load_csv_file(self, filename):
        csv_loader = CSV2JSON(input_file=filename)
        return csv_loader._load()

    # TODO: provide other file reading functionality as needed
