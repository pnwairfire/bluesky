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
        # TODO: In case 'start' and/or 'end' are specified in index,
        #   set self._max_days_out to 0 to ignore directories timestamped
        #   before 'start'?  (prob not, since ultimately we're concerned
        #   with the dates represented in the met files, not what's indicated
        #   in the directory names.)
        #self._max_days_out = 0

    def index(self, start=None, end=None):
        """

        kwargs:
         - start -- only consider met data after this date
         - end -- only consider met data before this date
        """
        start, end = self._fill_in_start_end(start, end)
        date_matcher = self._create_date_matcher(start, end)
        index_files = self._find_index_files(date_matcher)
        arl_files = self._parse_index_files(index_files)
        files_per_hour = self._determine_files_per_hour(arl_files)
        files = self._determine_file_time_windows(files_per_hour)
        files_per_hour, files = self._filter(files_per_hour, files, start, end)
        index_data = self._analyse(files_per_hour, files)
        self._write(index_data)

    def _filter(self, files_per_hour, files, start, end):
        if start and end:
            # need to filter files and files_per_hour separately
            # because some files may cross the start and/or end times
            #logging.debug("files (BEFORE): %s", files)
            #logging.debug("files_per_hour (BEFORE): %s", files_per_hour)
            files = self._filter_files(files, start, end)
            files_per_hour = {k:v for k, v in files_per_hour.items()
                if k >= start and k <= end}
            #logging.debug("files (AFTER): %s", files)
            #logging.debug("files_per_hour (AFTER): %s", files_per_hour)
        return files_per_hour, files

    ##
    ## start/end validation and filling in
    ##

    def _fill_in_start_end(self, start, end):
        if start or end:
            # Start can be specified without end (which would default to
            # today), but not vice versa
            if not start:
                raise ValueError("End date can't be specified without start")
            end = end or datetime.datetime.utcnow()
            if start > end:
                raise ValueError("'start' must be before 'end'")
            logging.debug('start: {}'.format(start.isoformat()))
            logging.debug('end: {}'.format(end.isoformat()))

        # else: both as undefined

        return start, end


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
