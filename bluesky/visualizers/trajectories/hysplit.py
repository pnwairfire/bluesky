"""bluesky.visualizers.disersion"""

__author__ = "Joel Dubowy"

__all__ = [
    'HysplitTrajectoriesVisualizer'
]
__version__ = "0.1.0"


import logging
import os

from bluesky import io
from bluesky.config import Config

class HysplitTrajectoriesVisualizer(object):
    """Generates KML from trajectores GeoJSON output file

    TODO: generate KML from scratch in order to:
      - use custom fire icons for location point features,
      - color coding trajectory lines by start height
      - group trajectories by start hours, and then by fire
      - customize popups
    """

    def __init__(self, fires_manager):
        self._fires_manager = fires_manager
        self._set_output_info()

    def _set_output_info(self):
        self._kml_file_name = None
        if self._fires_manager.trajectories:
            o = self._fires_manager.trajectories.get('output')
            if o and o.get('geojson_file_name') and o.get('directory'):
                self._geojson_file_name = os.path.join(o['directory'],
                    o['geojson_file_name'])
                self._kml_file_name = os.path.join(o['directory'],
                    Config().get('visualization', 'trajectories', 'hysplit',
                        'kml_file_name')
                )

            else:
                logging.warning("No trajectories GeoJSON file to convert to KML")

        else:
            raise RuntimeError("Hysplit trajectories doesn't appear to have been run")

    def run(self):
        r = {"output": {}}
        if self._kml_file_name:
            args = [
                'ogr2ogr', '-f', 'kml',
                self._kml_file_name,
                self._geojson_file_name
            ]
            io.SubprocessExecutor().execute(*args)

            r["output"] = {
                'kml_file_name': os.path.basename(self._kml_file_name),
                'directory': os.path.dirname(self._kml_file_name),
            }

        return r
