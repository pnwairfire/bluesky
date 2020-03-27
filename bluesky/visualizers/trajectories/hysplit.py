"""bluesky.visualizers.disersion"""

__author__ = "Joel Dubowy"

__all__ = [
    'HysplitTrajectoriesVisualizer'
]
__version__ = "0.1.0"


import os

from bluesky import io
from bluesky.config import Config

class HysplitTrajectoriesVisualizer(object):

    def __init__(self, fires_manager):
        self._fires_manager = fires_manager
        self._set_output_info()

    def _set_output_info(self):
        self._geojson_file_name = (self._fires_manager.trajectories
            and self._fires_manager.trajectories.get('geojson_file_name'))

        if not self._geojson_file_name:
            raise RuntimeError("No trajectories GeoJSON file to convert to KML")

        self._kml_file_name = os.path.join(
            os.path.dirname(self._geojson_file_name),
            Config().get('visualization', 'trajectories', 'hysplit',
                'kml_file_name')
        )


    def run(self):
        args = [
            'ogr2ogr', '-f', 'kml',
            self._kml_file_name,
            self._geojson_file_name
        ]
        io.SubprocessExecutor().execute(*args)

        return {
            'kml_file_name': self._kml_file_name
        }
