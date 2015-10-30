"""bluesky.arlfinder

This module finds arl met data files for a particular domain and time window.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from bluesky.datetimeutils import parse_datetimes

__all__ = [
    'ArlFinder'
]

class ArlFinder(object):
    def __init__(self, met_root_dir):
        # make sure met_root_dir is an existing directory
        try:
            if not met_root_dir or not os.path.isdir(met_root_dir):
                raise ValueError("{} is not a valid directory".format(met_root_dir))
        except TypeError:
            raise ValueError("{} is not a valid directory".format(met_root_dir))
        self._met_root_dir = met_root_dir

    def find(self, start, end):
        # TODO: for each hour in date range defined by start/end, look in
        # self._met_root_dir to find most recent met data file containing that
        # hour; return object containing domain id, gridspacing, boundary information
        # and list of file objects, each containing a datetime range with the arl file
        # to use for each range
        # Ex.
        #        {
        #            "domain" : "DRI6km",
        #            "grid_spacing_km": 6.0,
        #            "boundary": {
        #                "sw":{
        #                    "lat": ,
        #                    "lng":
        #                },
        #                "nw": {
        #                    "lat": ,
        #                    "lng":
        #                }
        #            },
        #            "files": [
        #                {
        #                    "file": "/DRI_6km/2014052912/wrfout_d2.2014052912.f00-11_12hr01.arl",
        #                    "first_hour": "2014-05-29T12:00:00",
        #                    "last_hour": "2014-05-29T23:00:00"
        #                },
        #                {
        #                    "file": "/DRI_6km/2014053000/wrfout_d2.2014053000.f00-11_12hr01.arl",
        #                    "first_hour": "2014-05-30T00:00:00",
        #                    "last_hour": "2014-05-30T11:00:00"
        #                }
        #            ],
        #        }        #  [
        raise NotImplementedError("findmetdata not yet implemented")
