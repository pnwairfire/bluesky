"""bluesky.loaders.firespider
"""

__author__ = "Joel Dubowy"

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

    def __init__(self, **config):
        super(JsonApiLoader, self).__init__(**config)

    def load(self):
        return json.loads(self.get(**self._config.get('query', {}))
