"""bluesky.met.arlindexer

This module indexes met data
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import json
import logging
import re
import sys
from collections import defaultdict

from bluesky import datautils
from .arlfinder import ArlFinder

__all__ = [
    'ArlIndexer'
]

class ArlIndexer(ArlFinder):

    def __init__(self, domain, met_root_dir, **config):
        """Constructor

        args:
         - domain -- domain identifier (ex. 'DRI2km')
         - met_root_dir -- root directory to search under

        config options:
         - mongodb_url -- format:
            'mongodb://[username:password@]host[:port][/[database][?options]]'"
         - output_file -- pathname (relative of absolute) of output file to
            save index data
        (see ArlFinder for it's config options)
        """
        # ArlFinder takes care of making sure met_root_dir exists
        super(ArlIndexer, self).__init__(met_root_dir, **config)
        self._domain = domain
        self._config = config

    # TODO: add '$' after date?
    ALL_DATE_MATCHER = re.compile('.*\d{10}')

    def index(self):
        index_files = self._find_index_files(self.ALL_DATE_MATCHER)
        arl_files = self._parse_index_files(index_files)
        files_per_hour = self._determine_files_per_hour(arl_files)
        files = self._determine_file_time_windows(files_per_hour)
        index_data = self._analyse(files_per_hour, files)
        self._write(index_data)

    ##
    ## Reorganizing data for index
    ##

    def _analyse(self, files_per_hour, files):
        # Note: reduce will be removed from py 3.0 standard library; though it
        # will be available in functools, use explicit loop instead
        dates = defaultdict(lambda: [])
        for dt in sorted(files_per_hour.keys()):
            dates[dt.date()].append(dt.hour)
        complete_dates = [d for d in dates if len(dates[d]) == 24]
        partial_dates = list(set(dates) - set(complete_dates))
        data = {
            'complete_dates': sorted(complete_dates),
            'partial_dates': sorted(partial_dates),
            'files': files
        }

        # TODO: slice and dice data in another way?
        return {self._domain: data}

    ##
    ## Writing results to db, file, or stdout
    ##

    def _write(self, index_data):
        # Note: using datautils.format_datetimes instead of defining
        #  a datetime encoder for json.dumps because datautils.format_datetimes
        #  handles formating both keys and values
        index_data = datautils.format_datetimes(index_data)
        if (not self._config.get('mongodb_url')
                and not self._config.get('output_file')):
            sys.stdout.write(json.dumps(index_data))
        else:
            succeeded = False

            for k in ('mongodb_url', 'output_file'):
                if self._config.get(k):
                    try:
                        m = getattr(self, '_write_to_{}'.format(k))
                        m(self._config[k], index_data)
                        succeeded = True
                    except Exception, e:
                        logging.error("Failed to write to {}: {}".format(
                            ' '.join(k.split('_')), e.message))
            if not succeeded:
                raise RuntimeError("Failed to record")

    def _write_to_mongodb_url(self, mongodb_url, index_data):
        # TODO: insert default database name to url if not already defined
        # TODO: write to db; log error, but don't fail?  or raise exception and
        #   let _write deal with it (like, if none of selected writes succeed,
        #   then raise exception, else just log error about failed write)
        raise NotImplementedError

    def _write_to_output_file(self, file_name, index_data):
        with open(file_name, 'w') as f:
            f.write(json.dumps(index_data))
