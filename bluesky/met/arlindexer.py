"""bluesky.met.arlindexer

This module indexes met data
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
import json
import re
import sys

from .arlfinder import ArlFinder

__all__ = [
    'ArlIndexer'
]


class ArlIndexer(object):

    def __init__(self, domain, met_root_dir, **config):
        """Constructor

        args:
         - domain -- Domain identifier (ex. 'DRI2km)
         - met_root_dir -- pattern that matches index files

        config options:
         - mongodb_url -- format 'mongodb://[username:password@]host[:port][/[database][?options]]'"
         - output_file --
         - index_filename_pattern -- default 'arl12hrindex.csv'
        """
        # ArlFinder takes care of making sure met_root_dir exists
        self._arl_finder = ArlFinder(met_root_dir, **config)
        self._config = config

    def index(self):
        self._find_index_files()
        self._analyse()
        self._write()

    ALL_DATE_MATCHER = re.compile('\d{8}')
    def _find_index_files(self):
        self._index_files = self._arl_finder._find_index_files(
            self.ALL_DATE_MATCHER)

    def _analyse(self):
        # TODO: ...
        pass

    def _write(self):
        if (not self._config.get('mongodb_url')
                and not self._config.get('output_file')):
            # TODO: use sys.stdout.write()
            pass

        else:
            if self._config.get('mongodb_url'):
                self._write_to_mongodb(self._config['mongodb_url'])
            if self._config.get('output_file'):
                self._write_to_file(self._config['output_file'])

    def _write_to_mongodb(self, mongodb_url):
        # TODO: insert default database name to url if not already defined
        # TODO: write to db; log error, but don't fail?  or raise exception and
        #   let _write deal with it (like, if none of selected writes succeed,
        #   then raise exception, else just log error about failed write)
        pass

    def _write_to_file(self, file_name):
        # TODO: write to file
        pass