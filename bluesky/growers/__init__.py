"""bluesky.growers"""

__author__ = "Joel Dubowy"

from afdatetime.parsing import parse as parse_dt

from bluesky.config import Config

class GrowerBase():

    def __init__(self, fires_manager):
        self._model = self.__class__.__module__.split('.')[-1]
        self._fires_manager = fires_manager

    def config(self, *keys, **kwargs):
        return Config().get('growth', self._model, *keys, **kwargs)


def to_date(dt):
    if dt:
        if hasattr(dt, 'lower'):
            dt = parse_dt(dt)

        # try/except in case parse_dt returned a date object
        try:
            return dt.date()
        except AttributeError as already_date_error:
            return dt
    # else, returns None