"""bluesky.arlfinder

This module finds arl met data files for a particular domain and time window.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

class ArlFinder(object):
    def __init__(self, met_root_dir):
        # make sure met_root_dir is an existing directory
        if not met_root_dir or not os.path.isdir(met_root_dir):
            raise ValueError("{} is not a valid directory".format(met_root_dir))
        self._met_root_dir = met_root_dir

    def find(self, start, end):
        # TODO: for each hour in date range defined by start/end, look in
        # self._met_root_dir to find most recent met data file containing that
        # hour; return list of datetime ranges with arl file to use for each range
        # Ex.
        #  [
        #     {"file": "...", "start": "...", "end": "..."}
        #  ]
        raise NotImplementedError("findmetdata not yet implemented")
