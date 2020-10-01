import json
import os
from collections import defaultdict

from bluesky import locationutils
from bluesky.models.fires import FireEncoder


class JsonOutputWriter(object):

    def __init__(self, config, fires_manager, output_dir):
        self._config = config
        self._fires_manager = fires_manager
        self._output_dir = output_dir
        self._set_file_name()

    def write(self):
        self._aggregate_locations()
        self._write_to_json()
        self._write_to_geojson()

    ## Setting & Getting Filenames

    @property
    def json_file_name(self):
        return self._json_file_name

    @property
    def geojson_file_name(self):
        return self._geojson_file_name

    def _aggregate_locations(self):
        locations_by_lat_lng = defaultdict(lambda: {"lines": []})
        for fire in self._fires_manager.fires:
            for loc in fire.locations:
                latlng = locationutils.LatLng(loc)
                new_loc = locations_by_lat_lng[(latlng.latitude, latlng.longitude)]
                # The following line only has to be done if not
                # new_loc.get('fire'), but doesn't hurt to do again
                new_loc.update(fire=fire, latlng=latlng)
                new_loc['lines'].extend(loc.get('trajectories', {}).get('lines', []))
        self._distinct_locations = list(locations_by_lat_lng.values())


    def _set_file_name(self):
        self._json_file_name = os.path.join(self._output_dir,
            self._config['json_file_name'])
        self._geojson_file_name = os.path.join(self._output_dir,
            self._config['geojson_file_name'])


    ## JSON file

    def _write_to_json(self):
        """Maintains bluesky's fires output structure, but including only
        trajectory data.
        """
        fires = defaultdict(lambda: {"locations": []})
        for loc in self._distinct_locations:
            fire = fires[loc['fire'].id]
            # The following line only has to be done if not
            # fire.get('id'), but doesn't hurt to do again
            fire["id"] = loc['fire'].id
            fire["locations"].append({
                "lines": loc['lines'],
                "lat": loc['latlng'].latitude,
                "lng": loc['latlng'].longitude
            })

        json_data = {
            "fires": list(fires.values())
        }
        self._write_file(self._json_file_name, json_data)


    ## GeoJSON file

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
        for loc in self._distinct_locations:
            geojson_data['features'].append(
                self._get_location_feature(loc['fire'], loc['latlng']))
            for line in loc['lines']:
                geojson_data['features'].append(
                    self._get_line_feature(loc['fire'], loc['latlng'], line))

        self._write_file(self._geojson_file_name, geojson_data)

    def _get_location_feature(self, fire, latlng):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [latlng.longitude, latlng.latitude]
            },
            "properties": {
                "fire_id": fire.id
            }
        }


    def _get_line_feature(self, fire, latlng, line):
        coords = [[p[1], p[0]] for p in line['points']]
        heights = [p[2] for p in line['points']]
        return {
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
        }


    ## Helpers

    def _write_file(self, filename, data):
        with open(filename, 'w') as f:
            f.write(json.dumps(data, cls=FireEncoder,
                indent=self._config['json_indent']))
