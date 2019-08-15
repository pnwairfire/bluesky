import datetime
import json
from collections import defaultdict

from bluesky import models, locationutils

class SummarizedFiresEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        # elif isinstance(obj, pd.DataFrame):
        #     return obj.to_json()

        return json.JSONEncoder.default(self, obj)


class SummarizedFire(dict):

    def __init__(self, fire):
        fire = models.fires.Fire(fire)

        self._set_lat_lng(fire)
        self._set_flat_summary(fire)
        self._set_timeprofiled_emissions(fire)

    def _set_lat_lng(self, fire):
        lat_lngs = [locationutils.LatLng(l) for l in fire.locations]

        def get_min_max(vals):
            return min(vals), max(vals), sum(vals) / len(vals)

        min_lat, max_lat, avg_lat = get_min_max([ll.latitude for ll in lat_lngs])
        min_lng, max_lng, avg_lng = get_min_max([ll.longitude for ll in lat_lngs])

        def format_str(mi, ma):
            return "{} to {}".format(mi, ma) if mi != ma else mi

        self['lat_lng'] = {
            'lat': {
                'min': min_lat,
                'max': max_lat,
                'avg': avg_lat,
                'pretty_str': format_str(min_lat, max_lat),
            },
            'lng': {
                'min': min_lng,
                'max': max_lng,
                'avg': avg_lng,
                'pretty_str': format_str(min_lng, max_lng)
            }
        }

    def _set_flat_summary(self, fire):
        active_areas = fire.active_areas
        locations = fire.locations
        self['flat_summary'] = {
            'id': fire.get('id'),
            'avg_lat': self['lat_lng']['lat']['avg'],
            'lat': self['lat_lng']['lat']['pretty_str'],
            'avg_lng':  self['lat_lng']['lng']['avg'],
            'lng': self['lat_lng']['lat']['pretty_str'],
            'total_consumption': fire.consumption['summary']['total'],
            'total_emissions': fire.emissions['summary']['total'],
            'PM2.5': fire.emissions['summary']['PM2.5'],
            'num_locations': len(locations),
            'total_area': sum([l['area'] for l in locations]),
            'start': min([aa['start'] for aa in active_areas]),
            'end': max([aa['end'] for aa in active_areas])
        }

    def _set_timeprofiled_emissions(self, fire):
        all_loc_emissions = defaultdict(lambda: defaultdict(lambda: 0.0))
        for aa in fire.active_areas:
            for loc in aa.locations:
                emissions = self._get_emissions(loc)
                per_species = {}
                for s in emissions:
                    for t in sorted(aa.get('timeprofile', {}).keys()):
                        d = aa['timeprofile'][t]
                        all_loc_emissions[t][s] += sum([
                            d[p]*emissions[s][p] for p in self.PHASES
                        ])

        self['timeprofiled_emissions'] = [
            dict(all_loc_emissions[t], dt=t) for t in sorted(all_loc_emissions.keys())
        ]

    PHASES = ['flaming', 'smoldering', 'residual']

    def _get_emissions(self, loc):
        # sum the emissions across all fuelbeds, but keep them separate by phase
        # we want species to be the outer dict and phase the innter
        emissions = {}
        for fb in loc['fuelbeds']:
            for p in self.PHASES:
                for s in fb['emissions'][p]:
                    emissions[s] = emissions.get(s, {})
                    # fb['emissions'][p][s] is an array of one value
                    emissions[s][p] = (emissions[s].get(p, 0.0)
                        + sum(fb['emissions'][p][s]))
        return emissions



def summarized_fires_by_id(fires):
    summarized_fires = [SummarizedFire(f) for f in fires]
    return {
        sf['flat_summary']['id']: sf for sf in summarized_fires
    }