"""bluesky.visualizers.trajectories.hysplit"""

__author__ = "Joel Dubowy"

__all__ = [
    'HysplitTrajectoriesVisualizer'
]
__version__ = "0.1.0"


import logging
import os

from bluesky.config import Config
from .hysplit_json_to_kml import transform_json_to_kml

class HysplitTrajectoriesVisualizer():
    """Generates KML from trajectores JSON output file
    """

    def __init__(self, fires_manager):
        self._fires_manager = fires_manager
        self._set_output_info()

    def _set_output_info(self):
        self._kml_file_name = None
        if self._fires_manager.trajectories:
            o = self._fires_manager.trajectories.get('output')
            if o and o.get('json_file_name') and o.get('directory'):
                self._json_file_name = os.path.join(o['directory'],
                    o['json_file_name'])
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
            transform_json_to_kml(self._json_file_name,self._kml_file_name)

            r["output"] = {
                'kml_file_name': os.path.basename(self._kml_file_name),
                'directory': os.path.dirname(self._kml_file_name),
            }

        return r
