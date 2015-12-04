"""bluesky.met.arlindexer

This module indexes met data
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import json
import logging
import os
import re
import socket
import sys
from collections import defaultdict

import pymongo

from bluesky import datautils
from .arlfinder import ArlFinder

__all__ = [
    'ArlIndexer',
    'MetFilesCollection',
    'MetDatesCollection'
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
        # TODO: if there's a way to get domain boundaries, do it here.
        #   (it can change, so would need ot get boundaries for each set
        #   of met files....probably too much pain to be worth it)
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

    # Error messages defined as constants in part for testing purposes
    END_WITHOUT_START_ERR_MSG = "End datetime can't be specified without start"
    START_AFTER_END_ERR_MSG = "Start datetime must be before end"
    def _fill_in_start_end(self, start, end):
        if start or end:
            # Start can be specified without end (which would default to
            # today), but not vice versa
            if not start:
                raise ValueError(self.END_WITHOUT_START_ERR_MSG)
            end = end or datetime.datetime.utcnow()
            if start > end:
                raise ValueError(self.START_AFTER_END_ERR_MSG)
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
        server_name = self._config.get('server_name') or socket.gethostname()
        data = {
            'server': server_name,
            'domain': self._domain,
            'complete_dates': sorted(complete_dates),
            'partial_dates': sorted(partial_dates),
            'root_dir': self._met_root_dir,
            'files': files
        }

        # TODO: slice and dice data in another way?
        return data

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
        # TODO: come up with good strategy to replace/update existing index (since
        #   files will be reomved, and thus need to be dissappeared from index; but
        #   since index is accross multiple servers, we only want to replace data
        #   representing current server).... <-- store in db under server as top key
        #   and matain alternate hierarchies with triggers???
        # TODO: possible data hierarchies to be stored in mongodb (possibly
        #   maintaining some via triggers?):
        #   - met > server > date
        #   - met > date > server
        #   - server > met > date
        #   - server > date > met
        #   - date > met > server
        #   - date > server > met
        MetFilesCollection(mongodb_url).update(index_data)

    def _write_to_output_file(self, file_name, index_data):
        with open(file_name, 'w') as f:
            f.write(json.dumps(index_data))


class ArlIndexDB(object):
    DB_NAME_EXTRACTOR_RE = re.compile('/([^/]*)$')
    DEFAULT_DB_NAME = 'arlindex'

    def __init__(self, mongodb_url='localhost'):
        """Constructor:

        args
         - mongodb_url -- mongodb url
            format 'mongodb://[username:password@]host[:port][/[database][?options]]'"
        """
        # TODO: raise exception if self.__class__.__name__ == 'ArlIndexDB' ???

        # insert default database name to url if not already defined
        m = self.DB_NAME_EXTRACTOR_RE.search(mongodb_url)
        if m and m.group(1):
            db_name = m.group(1)
        else:
            db_name = self.DEFAULT_DB_NAME
            mongodb_url = os.path.join(mongodb_url, db_name)
        logging.debug('mongodb url: %s', mongodb_url)
        logging.debug('db name: %s', db_name)

        self.client = pymongo.MongoClient(mongodb_url)
        self.db = self.client[db_name]

        # 'met_files' collection list available met files
        # per server per domain
        self.met_files = self.client[db_name]['met_files']
        # 'dates' collection lists dates available per domain
        # across  all servers
        self.dates = self.client[db_name]['dates']

        # TODO: call _ensure_indices here?
        # self._ensure_indices(self.met_files)
        # self._ensure_indices(self.dates)

    def _ensure_indices(self, collection):
        # handle 'INDEXED_FIELDS' not being defined for a collection
        fields = getattr(self, 'INDEXED_FIELDS', [])
        for f in fields:
            collection.ensure_index(f)

class MetFilesCollection(ArlIndexDB):

    INDEXED_FIELDS = ['server', 'domain']

    def update(self, index_data):
        if not index_data.get('server') or not index_data.get('domain'):
            raise ValueError("Index data must define 'server' and 'domain'")

        self._ensure_indices(self.met_files)  # TODO: call this in the init?

        # we want to update or insert
        query = {'server': index_data['server'], 'domain': index_data['domain']}
        self.met_files.update(query, index_data, upsert=True)

    def find(self, **query):
        """Find available files, by server and domain
        """
        r = self.met_files.find(filter=query)
        return [e.pop('_id') and e for e in r]

class MetDatesCollection(ArlIndexDB):

    INDEXED_FIELDS = ['domain']

    # TODO: build aggregation into the db as a trigger
    def compute(self):
        dates_by_domain = defaultdict(lambda: defaultdict(lambda: []))
        for d in self.met_files.find():
            dates_by_domain[d['domain']]['complete_dates'].extends(
                d['complete_dates'])
            dates_by_domain[d['domain']]['partial_dates'].extends(
                d['partial_dates'])

        # iterate through domains, removing from partial_dates any dates
        # that are in complete_dates, and create record for domain
        to_save = []
        for domain, data in dates_by_domain.items():
            partial_dates = list(
                set(data['partial_dates']) - set(data['complete_dates']))
            to_save.append({
                'domain': domain,
                'complete_dates': data['complete_dates'],
                'partial_dates': partial_dates
            })
        return to_save

    def compute_and_save(self):
        to_save = self.compute()

        self._ensure_indices(self.met_files)  # TODO: call this in the init?
        self._ensure_indices(self.dates)  # TODO: call this in the init?

        # TODO: is there a way to do a bulk write, opting for upsert
        #  on each item in to_save?
        for d in to_save:
            self.dates.update({'domain': d['domain']}, d, upsert=True)
        return to_save

    def find(self, domain=None):
        """Find available dates, by domain or across all dates
        """
        query = {'domain': domain} if domain else {}
        r = self.dates.find(filter=query)
        return [e.pop('_id') and e for e in r]

