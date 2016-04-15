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

import os

from bluesky.exceptions import BlueSkyConfigurationError

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

class BaseFileLoader(object):

    def __init__(self, **config):
        self._filename = config.get('file')
        if not self._filename:
            raise BlueSkyConfigurationError('Specify a file to load')
        if not os.path.isfile(self._filename):
            raise BlueSkyConfigurationError('File {} does not exist'.format(
                self._filename))

    # TODO: provide file reading functionality in this class, or just let
    #  subclasses take care of it?
