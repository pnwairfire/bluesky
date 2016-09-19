"""bluesky.loaders.firespider
"""

__author__ = "Joel Dubowy"

import datetime
import json
import os

from . import BaseApiLoader

__all__ = [
    'FileLoader'
]

class JsonApiLoader(BaseApiLoader):
    """Loads csv formatted SF2 fire and events data from filename

    TODO: move code into base class(es) - BaseApiLoader and/or
    BaseJsonLoader - and have JsonApiLoader inherit from one or both
    """

    DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S%Z'

    def __init__(self, **config):
        super(JsonApiLoader, self).__init__(**config)
        self._query = config.get('query', {})

        # Convert datetime.date objects to strings
        for k in self._query:
            if isinstance(self._query[k], datetime.date):
                self._query[k] = self._query[k].strftime(
                    self.DATETIME_FORMAT)
                # TODO: if no timezone info, add 'Z' to end of string ?

    def load(self):
        return json.loads(self.get(**self._query))
