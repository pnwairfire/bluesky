"""bluesky.met.arlfinder

This module finds arl met data files for a particular domain and time window.

Arl index files have a fairly standard format, but do differ in some ways.
For example, sometimes the list files are names only, sometimes they're
abslute paths, and sometimes they're filenames with a leading '/' (where
the leading '/' should be ignored.)

Example index file contents

$ cat /DRI_2km/2015110300/arl12hrindex.csv
filename,start,end,interval
wrfout_d3.2015110300.f00-11_12hr01.arl,2015-11-03 00:00:00,2015-11-03 11:00:00,12
wrfout_d3.2015110300.f12-23_12hr02.arl,2015-11-03 12:00:00,2015-11-03 23:00:00,12
wrfout_d3.2015110300.f24-35_12hr03.arl,2015-11-04 00:00:00,2015-11-04 11:00:00,12
wrfout_d3.2015110300.f36-47_12hr04.arl,2015-11-04 12:00:00,2015-11-04 23:00:00,12
wrfout_d3.2015110300.f48-59_12hr05.arl,2015-11-05 00:00:00,2015-11-05 11:00:00,12
wrfout_d3.2015110300.f60-71_12hr06.arl,2015-11-05 12:00:00,2015-11-05 23:00:00,12

$ cat /DRI_6km/2015110300/arl12hrindex.csv
filename,start,end,interval
wrfout_d2.2015110300.f00-11_12hr01.arl,2015-11-03 00:00:00,2015-11-03 11:00:00,12
wrfout_d2.2015110300.f12-23_12hr02.arl,2015-11-03 12:00:00,2015-11-03 23:00:00,12
wrfout_d2.2015110300.f24-35_12hr03.arl,2015-11-04 00:00:00,2015-11-04 11:00:00,12
wrfout_d2.2015110300.f36-47_12hr04.arl,2015-11-04 12:00:00,2015-11-04 23:00:00,12
wrfout_d2.2015110300.f48-59_12hr05.arl,2015-11-05 00:00:00,2015-11-05 11:00:00,12
wrfout_d2.2015110300.f60-71_12hr06.arl,2015-11-05 12:00:00,2015-11-05 23:00:00,12

$ cat /bluesky/data/NAM/2015110300/NAM36_ARL_2015110300_index.csv
filename,start,end,interval
/bluesky/met/NAM/ARL/2015/11/nam_forecast-2015110300_00-36hr.arl,2015-11-03 00:00:00,2015-11-04 12:00:00,36

$ cat /bluesky/data/NAM/2015110300/NAM84_ARL_2015110300_index.csv
filename,start,end,interval
/bluesky/met/NAM/ARL/2015/11/nam_forecast-2015110300_00-84hr.arl,2015-11-03 00:00:00,2015-11-06 12:00:00,84

$ cat /bluesky/data/GFS/2015110300/GFS192_ARL_index.csv
filename,start,end,interval
/bluesky/data/gfs/2015110300/gfs_forecast-2015110300_000-192hr.arl,2015-11-03 00:00:00,2015-11-11 00:00:00,192

$ cat /bluesky/data/NAM4km/2015110300/nam4km_arlindex.csv
filename,start,end,interval
/hysplit.t00z.namsf00.CONUS,2015-11-03 01:00:00,2015-11-03 06:00:00,6
/hysplit.t00z.namsf06.CONUS,2015-11-03 07:00:00,2015-11-03 12:00:00,6
/hysplit.t00z.namsf12.CONUS,2015-11-03 13:00:00,2015-11-03 18:00:00,6
/hysplit.t00z.namsf18.CONUS,2015-11-03 19:00:00,2015-11-04 00:00:00,6

$ cat /storage/NWRMC/4km/2015102900/arl12hrindex.csv
filename,start,end,interval
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102800.f24-35_12hr02.arl,2015-10-29 00:00:00,2015-10-29 11:00:00,12
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102900.f12-23_12hr01.arl,2015-10-29 12:00:00,2015-10-29 23:00:00,12
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102900.f24-35_12hr02.arl,2015-10-30 00:00:00,2015-10-30 11:00:00,12
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102900.f36-47_12hr03.arl,2015-10-30 12:00:00,2015-10-30 23:00:00,12
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102900.f48-59_12hr04.arl,2015-10-31 00:00:00,2015-10-31 11:00:00,12
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102900.f60-71_12hr05.arl,2015-10-31 12:00:00,2015-10-31 23:00:00,12
/storage/NWRMC/4km/2015102900/wrfout_d3.2015102900.f72-83_12hr06.arl,2015-11-01 00:00:00,2015-11-01 11:00:00,12

$ cat /storage/NWRMC/1.33km/2015110300/arl12hrindex.csv
filename,start,end,interval
/storage/NWRMC/1.33km/2015110300/wrfout_d4.2015110200.f24-35_12hr02.arl,2015-11-03 00:00:00,2015-11-03 11:00:00,12
/storage/NWRMC/1.33km/2015110300/wrfout_d4.2015110300.f12-23_12hr01.arl,2015-11-03 12:00:00,2015-11-03 23:00:00,12
/storage/NWRMC/1.33km/2015110300/wrfout_d4.2015110300.f24-35_12hr02.arl,2015-11-04 00:00:00,2015-11-04 11:00:00,12
/storage/NWRMC/1.33km/2015110300/wrfout_d4.2015110300.f36-47_12hr03.arl,2015-11-04 12:00:00,2015-11-04 23:00:00,12
/storage/NWRMC/1.33km/2015110300/wrfout_d4.2015110300.f48-59_12hr04.arl,2015-11-05 00:00:00,2015-11-05 11:00:00,12

$ cat /storage/NWRMC/4km/2015110300/arl12hrindex.csv
filename,start,end,interval
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110200.f24-35_12hr02.arl,2015-11-03 00:00:00,2015-11-03 11:00:00,12
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110300.f12-23_12hr01.arl,2015-11-03 12:00:00,2015-11-03 23:00:00,12
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110300.f24-35_12hr02.arl,2015-11-04 00:00:00,2015-11-04 11:00:00,12
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110300.f36-47_12hr03.arl,2015-11-04 12:00:00,2015-11-04 23:00:00,12
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110300.f48-59_12hr04.arl,2015-11-05 00:00:00,2015-11-05 11:00:00,12
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110300.f60-71_12hr05.arl,2015-11-05 12:00:00,2015-11-05 23:00:00,12
/storage/NWRMC/4km/2015110300/wrfout_d3.2015110300.f72-83_12hr06.arl,2015-11-06 00:00:00,2015-11-06 11:00:00,12
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import datetime
#import glob
import logging
import os
import re

from bluesky import datautils
from bluesky.datetimeutils import parse_datetimes, parse_utc_offset
from bluesky.io import CSV2JSON

__all__ = [
    'ArlFinder'
]

ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(days=1)

class ArlFinder(object):

    DEFAULT_INDEX_FILENAME_PATTERN = "arl12hrindex.csv"
    DEFAULT_MAX_DAYS_OUT = 4

    def __init__(self, met_root_dir, **config):
        """Constructor

        args:
         - met_root_dir -- restrict search to files under this dir
         - arl_index_filename_pattern -- pattern that matches index files
        """
        # make sure met_root_dir is an existing directory
        try:
            # TODO: make sure os.path.isdir prptects against injects attacks
            #  Ex:  os.path.isdir('/ && rm -rf /')
            #  I tested on OSX and it worked safely, but not sure about other
            #  platforms
            if not met_root_dir or not os.path.isdir(met_root_dir):
                raise ValueError("{} is not a valid directory".format(met_root_dir))
        except TypeError:
            raise ValueError("{} is not a valid directory".format(met_root_dir))
        self._met_root_dir = met_root_dir
        self._index_filename_matcher = re.compile(
            config.get("index_filename_pattern") or
            self.DEFAULT_INDEX_FILENAME_PATTERN)
        logging.debug("Looking for index filenames mathing pattern '%s'",
            self._index_filename_matcher.pattern)
        self._max_days_out = int(config.get("max_days_out",
            self.DEFAULT_MAX_DAYS_OUT))

    def find(self, start, end):
        """finds met data spanning start/end time window

        args:
         - start -- UTC start of time window
         - end -- UTC end of time window

        This method searches for all arl met files under self._met_root_dir
        with data spanning the given time window and determines which file
        to use for each hour in the window.  The goal is to use the most
        recent met data for any given hour.  It returns a dict containing
        a list of file objects, each containing a datetime range with the arl file
        to use for each range
        Ex.
               {
                   "files": [
                       {
                           "file": "/DRI_6km/2014052912/wrfout_d2.2014052912.f00-11_12hr01.arl",
                           "first_hour": "2014-05-29T12:00:00",
                           "last_hour": "2014-05-29T23:00:00"
                       },
                       {
                           "file": "/DRI_6km/2014053000/wrfout_d2.2014053000.f00-11_12hr01.arl",
                           "first_hour": "2014-05-30T00:00:00",
                           "last_hour": "2014-05-30T11:00:00"
                       }
                   ],
               }

        TODO: extract grid information as well (boundary, spacing, domain),
          and include in return object.
          Ex.
               {
                   "files": [
                        ...
                    ],
                    "grid": {
                        "spacing": 6.0,
                        "boundary": {
                            "ne": {
                                "lat": 45.25,
                                "lng": -106.5
                            },
                            "sw": {
                                "lat": 27.75,
                                "lng": -131.5
                            }
                        }
                    }
                }
          where 'domain' would be set to 'LatLon' if spacing is in degrees
        """
        if not start or not end:
            raise ValueError('Start and end times must be defined to find arl data')

        date_matcher = self._create_date_matcher(start, end)
        index_files = self._find_index_files(date_matcher)
        arl_files = self._parse_index_files(index_files)
        files_per_hour = self._determine_files_per_hour(arl_files)
        files = self._determine_file_time_windows(files_per_hour)
        files = self._filter_files(files, start, end)
        files = datautils.format_datetimes(files)

        return {'files': files}

    ##
    ## Finding Index Files
    ##

    def _create_date_matcher(self, start, end):
        """Returns a compiled regex object that matches %Y%m%d date strings
        for all dates between start and end, plus 4 days prior

        The 4 days prior are included in since
        """
        num_days = (end.date()-start.date()).days
        dates_to_match = [start + ONE_DAY*i
            for i in range(-self._max_days_out, num_days+1)]
        return re.compile(".*({}).*".format(
            '|'.join([dt.strftime('%Y%m%d') for dt in dates_to_match])))

    def _find_index_files(self, date_matcher):
        """Searches for index files under dir

        Example index file locations:

            /DRI_2km/2015110300/arl12hrindex.csv
            /DRI_6km/2015110300/arl12hrindex.csv
            /bluesky/data/NAM/2015110300/NAM36_ARL_2015110300_index.csv
            /bluesky/data/NAM/2015110300/NAM84_ARL_2015110300_index.csv
            /bluesky/data/GFS/2015110300/GFS192_ARL_index.csv
            /bluesky/data/NAM4km/2015110300/nam4km_arlindex.csv
            /storage/NWRMC/4km/2015102900/arl12hrindex.csv
            /storage/NWRMC/1.33km/2015110300/arl12hrindex.csv
            /storage/NWRMC/4km/2015110300/arl12hrindex.csv
        """
        index_files = []
        for root, dirs, files in os.walk(self._met_root_dir):
            #logging.debug('Root: {}'.format(root))
            if date_matcher.match(root):
                for f in files:
                    if self._index_filename_matcher.match(f): #(os.path.basename(f)):
                        logging.debug('found index file: {}'.format(f))
                        index_files.append(os.path.join(root, f))
        logging.debug('Found {} index files'.format(len(index_files)))
        return index_files

    ##
    ## Parsing Index Files
    ##

    def _parse_index_files(self, index_files):
        """Iterates through arl index files, iterating each

        args:
         - index_files -- list of index file names
        """
        arl_files = []
        for f in index_files:
            #logging.debug(files_per_hour)
            arl_files.extend(self._parse_index_file(f))
        return arl_files

    def _parse_index_file(self, index_file):
        """Parses arl index files, extracting each arl file with its start
        hour and last our

        args:
         - files_per_hour -- lists which met file to use for each hour
         - index_file -- pathname of index file to parse
        """
        arl_files = []
        for row in CSV2JSON(input_file=index_file)._load():
            tw = parse_datetimes(row, 'start', 'end')
            f = self._get_file_pathname(index_file, row['filename'])
            if f:
                arl_files.append(
                    dict(file=f, first_hour=tw['start'], last_hour=tw['end']))
        return arl_files

    def _get_file_pathname(self, index_file, name):
        """Returns absolute pathname of arl file listed in the index file

        args:
         - index_file -- index file listing arl file
         - name -- name of arl file, as listed in index file
        """
        f = os.path.abspath(name)
        if os.path.isfile(f):
            return f

        f = os.path.join(os.path.dirname(index_file), name.strip('/'))
        if os.path.isfile(f):
            return f

        # raise ValueError("Can't find arl file {} listed in {}".format(
        #     name, index_file))

    ##
    ## Mapping hours to arl files and vice versa
    ##

    def _determine_files_per_hour(self, arl_files):
        """Determines which arl file has the most recent data for each hour

        Note: This method assumes that the files, when listed chronolofically,
        are also ordered alphabetically, since the pathnames should be
        identical other than datetime information embedded in them.
        """
        files_per_hour = {}
        for f_dict in arl_files:
            dt = f_dict['first_hour']
            while dt <= f_dict['last_hour']:
                if not files_per_hour.get(dt) or files_per_hour[dt] < f_dict['file']:
                    files_per_hour[dt] = f_dict['file']
                dt += ONE_HOUR
        return files_per_hour

    def _determine_file_time_windows(self, files_per_hour):
        """Determines time windows for which each arl file should be used.

        Note: Assumes ...
        """
        files = []
        for dt, f in sorted(files_per_hour.items(), key=lambda e: e[0]):
            if (not files or (dt - files[-1]['last_hour']) > ONE_HOUR or
                    files[-1]['file'] != f):
                files.append({'file': f, 'first_hour':dt, 'last_hour': dt})
            else:
                files[-1]['last_hour'] = dt
        return files

    ##
    ## Filtering and Formating
    ##

    def _filter_files(self, files, start, end):
        return [
            f for f in files if
                (f['first_hour'] >= start and f['first_hour'] <= end) or
                (f['last_hour'] >= start and f['last_hour'] <= end)
        ]
