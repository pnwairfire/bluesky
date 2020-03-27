import json
import os

from bluesky import locationutils
from bluesky.models.fires import FireEncoder


class JsonOutputWriter(object):

    def __init__(self, config, fires_manager, output_dir):
        self._config = config
        self._fires_manager = fires_manager
        self._output_dir = output_dir

    def write(self):
        self._write_to_json()
        self._write_to_geojson()

    def _write_to_json(self):
        json_data = {"fires": []}
        for fire in self._fires_manager.fires:
            json_data["fires"].append({"id": fire.id, "locations": []})
            for loc in fire.locations:
                latlng = locationutils.LatLng(loc)
                json_data["fires"][-1]["locations"].append({
                    "lines": loc['trajectories']['lines'],
                    "lat": latlng.latitude,
                    "lng": latlng.longitude
                })

        filename = os.path.join(self._output_dir,
            self._config['json_file_name'])
        with open(filename, 'w') as f:
            f.write(json.dumps(json_data, cls=FireEncoder,
                indent=self._config['json_indent']))

    def _write_to_geojson(self):
        pass