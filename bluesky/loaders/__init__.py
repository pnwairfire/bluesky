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
import json
import logging
import os
import urllib
import shutil

from afweb import auth
from pyairfire.io import CSV2JSON

from bluesky import datetimeutils
from bluesky.exceptions import BlueSkyConfigurationError

__author__ = "Joel Dubowy"

__all__ = [
    'BaseApiLoader',
    'BaseFileLoader'
]

class BaseLoader(object):

    def __init__(self, **config):
        self._config = config

    def _write_data(self, saved_data_filename, data):
        if filename:
            try:
                with open(filename) as f:
                    f.write(data)
            except Exception as e:
                logging.warn(
                    "Failed to write loaded data to %s - %s", filename, e)

    def _copy_file(self, original, saved_copy_filename):
        if saved_copy_filename:
            try:
                shutil.copyfile(original, saved_copy_filename)
            except Exception as e:
                logging.warn("Failed to copy %s to %s - %s",
                    original, saved_copy_filename, e)


##
## Files
##

class BaseFileLoader(BaseLoader):

    def __init__(self, **config):
        self._filename = config.get('file')
        if not self._filename:
            raise BlueSkyConfigurationError(
                "Fires file to load not specified")
        if not os.path.isfile(self._filename):
            raise BlueSkyConfigurationError("Fires file to "
                "load {} does not exist".format(self._filename))
        self._saved_copy_filename = config.get('saved_copy_file')

        self._events_filename = None
        if config.get('events_file'):
            self._events_filename = config['events_file']
            if not os.path.isfile(self._events_filename):
                raise BlueSkyConfigurationError("Fire events file to load {} "
                    "does not exist".format(self._events_filename))
        self._saved_copy_events_filename = config.get('saved_copy_events_file')

    ##
    ## File IO
    ##


    def _load_csv_file(self, filename, saved_copy_filename=None):
        self._copy_file(filename, saved_copy_filename)
        csv_loader = CSV2JSON(input_file=filename)
        return csv_loader._load()

    def _load_json_file(self, filename, saved_copy_filename=None):
        self._copy_file(filename, saved_copy_filename)
        with open(filename, 'r') as f:
            return json.loads(f.read())

    # TODO: provide other file reading functionality as needed

##
## API
##

class BaseApiLoader(BaseLoader):

    DEFAULT_KEY_PARAM = "_k"
    DEFAULT_AUTH_PROTOCOL = "afweb"
    DEFAULT_REQUEST_TIMEOUT = 10 # seconds

    def __init__(self, **config):
        self._endpoint = config.get('endpoint')
        if not self._endpoint:
            raise BlueSkyConfigurationError(
                "Json API not specified")

        self._key = config.get('key')
        self._secret = config.get('secret')
        # you can have a key without a secret, but not vice versa
        if self._secret and not self._key:
            raise BlueSkyConfigurationError(
                "Api key must be specified if secret is specified")

        self._key_param = config.get('key_param',
            self.DEFAULT_KEY_PARAM)
        self._auth_protocol = config.get('auth_protocol',
            self.DEFAULT_AUTH_PROTOCOL)
        self._request_timeout = config.get('request_timeout',
            self.DEFAULT_REQUEST_TIMEOUT)

    def get(self, saved_data_filename=None, **query):
        if self._secret:
            if self._auth_protocol == 'afweb':
                url = self._form_url(**query)
                url = auth.sign_url(url, self._key, self._secret)
            else:
                raise NotImplementedError(
                    "{} auth protocol not supported".format(
                    self._auth_protocol))
        else:
            if self._key:
                params[self._key_param] = self._key
            url = self._form_url(**query)

        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, None, self._request_timeout)
        body =  resp.read().decode('ascii')

        self._write_data(saved_data_filename, body)

        return body

    def _form_url(self, **query):
        query_param_tuples = []
        for k, v in query.items():
            if isinstance(v, list):
                query_param_tuples.extend([(k, _v) for _v in v])
            else:
                query_param_tuples.append((k, v))
        query_string = '&'.join(sorted([
            "%s=%s"%(k, v) for k, v in query_param_tuples]))
        return "{}?{}".format(self._endpoint, query_string)
