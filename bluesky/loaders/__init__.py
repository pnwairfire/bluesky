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
            # default to current date
            self._date_time = datetime.date.today()


class BaseFileLoader(BaseLoader):

    def __init__(self, **config):
        super(BaseFileLoader, self).__init__(**config)
        self._filename = config.get('file')
        if not self._filename:
            raise BlueSkyConfigurationError('Specify a file to load')

        # if file does exist with, try filling in datetime codes
        if not os.path.isfile(self._filename):
            self._filename = self._date_time.strftime(self._filename)

        # if it still doesn't exist, raise exception
        if not os.path.isfile(self._filename):
            raise BlueSkyConfigurationError('File {} does not exist'.format(
                self._filename))

    # TODO: provide file reading functionality in this class, or just let
    #  subclasses take care of it?
