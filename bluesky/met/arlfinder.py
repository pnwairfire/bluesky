"""bluesky.met.arlfinder

This module finds arl met data files for a particular domain and time window.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

#import glob
import logging
import os

from bluesky.datetimeutils import parse_datetimes

__all__ = [
    'ArlFinder'
]

class ArlFinder(object):
    def __init__(self, met_root_dir, **config):
        """Constructor

        args:
         - met_root_dir --
         - arl_index_filename --
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
        self._arl_index_filename = config.get("index_filename", "arl12hrindex.csv")

    def find(self, start, end):
        """finds met data spanning start/end time window

        args:
         - start -- UTC start of time window
         - end -- UTC end of time window

        This method searches for all arl met files under self._met_root_dir
        with data spanning the given time window and determines which file
        to use for each hour in the window.  The goal is to use the most
        recent met data for any given hour.  It returns a dict containing domain id, gridspacing, boundary information
        and list of file objects, each containing a datetime range with the arl file
        to use for each range
        Ex.
               {
                   "boundary": {
                       "sw":{
                           "lat": ,
                           "lng":
                       },
                       "nw": {
                           "lat": ,
                           "lng":
                       }
                   },
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
        """
        index_files = self._find_index_files(self._met_root_dir)

        raise NotImplementedError("findmetdata not yet implemented")

    def _find_index_files(self, dir, index_files=None):
        index_files = index_files or []
        for root, dirs, files in os.walk(dir):
            logging.debug('Root: {}'.format(root))
            for f in files:
                if os.path.basename(f) == self._arl_index_filename:
                    index_files.append(os.path.join(root, f))
            for d in dirs:
                index_files.extend(self._find_index_files(
                    os.path.join(root, d), index_files=files))
        return index_files
