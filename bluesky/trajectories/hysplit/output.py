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
        """Maintains bluesky's fires output structure, but including only
        trajectory data.
        """
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

        self._write_file(self._config['json_file_name'], json_data)

    def _write_to_geojson(self):
        """Flattens trajectory data into a FeatureCollection of trajectory
        line Features (one Feature per line)

        TODO: group by fire, and then by location, and then by start hour,
        if possible.
        """
        geojson_data = {
            "type": "FeatureCollection",
            "features": []
        }
        for fire in self._fires_manager.fires:
            for loc in fire.locations:
                latlng = locationutils.LatLng(loc)
                for line in loc['trajectories']['lines']:
                    coords = [[p[1], p[0]] for p in line['points']]
                    heights = [p[2] for p in line['points']]
                    geojson_data['features'].append({
                        "type": "Feature",
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords
                        },
                        "properties": {
                            "fire_id": fire.id,
                            "location_lat": latlng.latitude,
                            "location_lng": latlng.longitude,
                            "start_hour": line['start'],
                            "heights": heights
                        }
                    })

        self._write_file(self._config['geojson_file_name'], geojson_data)

    def _write_file(self, filename, data):
        filename = os.path.join(self._output_dir, filename)
        with open(filename, 'w') as f:
            f.write(json.dumps(data, cls=FireEncoder,
                indent=self._config['json_indent']))
