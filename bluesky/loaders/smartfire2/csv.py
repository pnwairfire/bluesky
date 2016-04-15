"""bluesky.loaders.smartfire.csv
"""

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import os

from pyairfire.io import CSV2JSON

from bluesky.loaders import BaseFileLoader

__all__ = [
    'FileLoader'
]

class FileLoader(BaseFileLoader):

    def __init__(self, **config):
        super(FileLoader, self).__init__()
        self._events_by_id = []
        if config.get('events_file'):
            self._load_events_file(config['events_file'])

    def load(self):
        fires = self._load_csv_file(self._filename)
        if self._events_by_id:
            for f in fires:
                if f.get('event_id') and f.get('event_id') in self.events
        return fires

    def _load_events_file(self, events_filename):
        if not os.path.isfile(events_filename):
            raise BlueSkyConfigurationError('File {} does not exist'.format(
                events_filename))
        events = self._load_csv_file(events_filename)
        self._events_by_id = { e.pop('id'): e for e in events}

    def _load_csv_file(self, filename):
        csv_loader = CSV2JSON(input_file=events_filename)
        return csv_loader._load()