"""bluesky.loaders

The loader packages and classes should be organized and named such that, given
the source name (e.g. 'FireSpider'), format (e.g. 'json'), and 'type' (e.g.
'file'), bluesky.modules.load can dynamically import the module with:

    >>> loader_module importlib.import_module(
        'bluesky.loaders.<source_name_to_lower_case>')'

and then get the loading class with:

    >>> getattr(loader_module,
            '<format_capitalized><source_type_capitalized>Loader')

For example, the firespider json file loader is in module
bluesky.loaders.firespider and is called JsonFileLoader
"""

import abc
import datetime
import json
import logging
import os
import urllib
import shutil

from afweb import auth
from pyairfire.io import CSV2JSON

from bluesky import datetimeutils
from bluesky.datetimeutils import parse_datetime, parse_utc_offset
from bluesky.exceptions import (
    BlueSkyConfigurationError, BlueSkyUnavailableResourceError
)
from bluesky.models.fires import Fire

__author__ = "Joel Dubowy"

__all__ = [
    'BaseApiLoader',
    'BaseFileLoader'
]

class BaseLoader(object):

    def __init__(self, **config):
        self._config = config

        # start and end times, to use in filtering activity windows
        self._start = self._config.get('start')
        self._end = self._config.get('end')
        self._start = self._start and parse_datetime(self._start, 'start')
        self._end = self._end and parse_datetime(self._end, 'end')
        if self._start and self._end and self._start > self._end:
            raise BlueSkyConfigurationError(self.START_AFTER_END_ERROR_MSG)

        self._saved_copy_filename = (self._config.get('saved_copy_file')
            or self._config.get('saved_data_file'))

    def load(self):
        data = self._load()
        self._save_copy(data)

        fires = self._marshal(data)
        # cast each fire to Fire object, in case child class
        #   did override _marshal but didn't return Fire objects?
        # TODO: support config setting 'skip_failures'
        fires = [Fire(f) for f in fires]
        fires = self._prune(fires)

        return fires

    ## Marshal

    def _marshal(self, data):
        """Hook for child classes to marshal input data to Fire objects
        """
        return data

    ## Pruning

    def _prune(self, fires):
        """Filters out activity windows that are outside of time range.
        """
        for fire in fires:
            # TODO: support config setting 'skip_failures'
            for a in fire['activity']:
                a['active_areas'] = [aa for aa in a.active_areas
                    if self._within_time_range(aa)]
            fire['activity'] = [a for a in fire['activity'] if a.active_areas]
        fires = [f for f in fires if f['activity']]

        return fires

    def _within_time_range(self, active_area):
        """
        Note that all times in the activity objects (activity 'start'
        and 'end' times, as well as timeprofile and hourly_frp keys)
        are already in local time.

        Also note that, though unlikely, the locations (specified points
        and/or perimeter) in the active area could have different utc offsets.
        """
        if active_area.get('start') and active_area.get('end'):
            utc_offsets = set([self._get_utc_offset(loc)
                for loc in active_area.locations])

            # convert to datetime objects in place
            active_area['start'] = parse_datetime(active_area.get('start'), 'start')
            active_area['end'] = parse_datetime(active_area.get('end'), 'end')

            is_within = False
            for utc_offset in utc_offsets:
                # the activity object's 'start' and 'end' will be in local time;
                # convert them to UTC to compare with start/end query parameters
                utc_start = active_area['start'] - utc_offset
                utc_end = active_area['end'] - utc_offset

                is_within = is_within or ((not self._start or utc_end >= self._start) and
                    (not self._end or utc_start <= self._end ))

            return is_within

        return False # not necessary, but makes code more readable

    def _get_utc_offset(self, location):
        utc_offset = location.get('utc_offset')
        if utc_offset:
            return datetime.timedelta(hours=parse_utc_offset(utc_offset))
        else:
            return datetime.timedelta(0)

    ## Saving copy of data

    def _save_copy(self, data):
        if self._saved_copy_filename:
            try:
                with open(self._saved_copy_filename, 'w') as f:
                    f.write(json.dumps(data))
            except Exception as e:
                logging.warning("Failed to write loaded data to %s - %s",
                    self._saved_copy_filename, e)


##
## Files
##

class BaseFileLoader(BaseLoader, metaclass=abc.ABCMeta):

    def __init__(self, **config):
        super(BaseFileLoader, self).__init__(**config)

        self._filename = config.get('file')
        if not self._filename:
            raise BlueSkyConfigurationError(
                "Fires file to load not specified")
        if not os.path.isfile(self._filename):
            raise BlueSkyUnavailableResourceError("Fires file to "
                "load {} does not exist".format(self._filename))

    def _save_copy(self, data):
        # initially try to just copy file; if fail, then use super
        # to write to file
        if self._saved_copy_filename:
            try:
                shutil.copyfile(self._filename, self._saved_copy_filename)
            except Exception as e:
                logging.warning(
                    "Failed to copy %s to %s - %s. Will attempt write to file",
                    self._filename, self._saved_copy_filename, e)
                super()._save_copy(data)


class BaseJsonFileLoader(BaseFileLoader):
    """Loads JSON formatted fire and events data from file
    """

    def _load(self):
        with open(self._filename, 'r') as f:
            return json.loads(f.read())


class BaseCsvFileLoader(BaseFileLoader):
    """Loads csv formatted fire and events data from file
    """

    def _load(self):
        csv_loader = CSV2JSON(input_file=self._filename)
        return csv_loader._load()


##
## API
##

class BaseApiLoader(BaseLoader):

    DEFAULT_KEY_PARAM = "_k"
    DEFAULT_AUTH_PROTOCOL = "afweb"
    DEFAULT_REQUEST_TIMEOUT = 10 # seconds

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

    def __init__(self, **config):
        super(BaseApiLoader, self).__init__(**config)

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

        self._query = config.get('query', {})
        # Convert datetime.date objects to strings
        for k in self._query:
            if isinstance(self._query[k], datetime.date):
                self._query[k] = self._query[k].strftime(
                    self.DATETIME_FORMAT)
                # TODO: if no timezone info, add 'Z' to end of string ?



    def _get(self):
        if self._secret:
            if self._auth_protocol == 'afweb':
                url = self._form_url()
                url = auth.sign_url(url, self._key, self._secret)
            else:
                raise NotImplementedError(
                    "{} auth protocol not supported".format(
                    self._auth_protocol))
        else:
            if self._key:
                params[self._key_param] = self._key
            url = self._form_url()

        req = urllib.request.Request(url)

        try:
            resp = urllib.request.urlopen(req, None, self._request_timeout)

        except urllib.request.HTTPError as e:
            # TODO: should we do this check? any other codes to
            # raise BlueSkyUnavailableResourceError for?
            if e.getcode() == 404:
                raise BlueSkyUnavailableResourceError(
                    "Unavailable resource for loading: {}".format(url))
            raise

        # else if URLError (e.g. hostname doesn't exist -
        #   'nodename nor servname provided, or not known'), then
        #   there's no use in retrying
        # TODO: handleany other errors?
        #   - CertificateError (e.g. "hostname 'www.googlesds.com' doesn't match either of '*.dadapro.com', 'dadapro.com'"")
        #   - other???

        body =  resp.read().decode('ascii')

        return body

    def _form_url(self):
        query_param_tuples = []
        for k, v in self._query.items():
            if isinstance(v, list):
                query_param_tuples.extend([(k, _v) for _v in v])
            else:
                query_param_tuples.append((k, v))
        query_string = '&'.join(sorted([
            "%s=%s"%(k, v) for k, v in query_param_tuples]))
        return "{}?{}".format(self._endpoint, query_string)

class BaseJsonApiLoader(BaseApiLoader):
    """Loads JSON formatted fire and events data from file
    """

    def _load(self):
        return json.loads(self._get())
