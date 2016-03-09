"""bluesky.process

# TODO: rename this module and move it?
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import datetime

__all__ = [
    "RunTimeRecorder"
]

class RunTimeRecorder(object):
    """Records run time information in dict that RunTimeRecorder is
    instantiated with.

    TODO: rename this module or move this class to a more appropriate
      module...or, move this class to another more general-purpose
      package (like pyairfire).
    """

    def __init__(self, rt_dict):
        if not isinstance(rt_dict, dict):
            raise ValueError(
                "RunTimeRecorder must be instantiated with a dict object")
        self._rt_dict = rt_dict

    def __enter__(self):
        self._start = datetime.datetime.utcnow()

    def __exit__(self, e_type, value, tb):
        end = datetime.datetime.utcnow()
        rt = end - self._start
        hours = rt.seconds / 3600 + 24*rt.days
        remaining_seconds = rt.seconds % 3600
        minutes = remaining_seconds / 60
        seconds = remaining_seconds % 60
        self._rt_dict.update({
            "start": self._format(self._start),
            "end": self._format(end),
            "total": "{}h {}m {}s".format(hours, minutes, seconds)
        })

    def _format(self, dt):
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
