import datetime
import json
from collections import defaultdict

from bluesky import models, locationutils
from bluesky.modules import fuelbeds


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
        self._set_per_location_data(fire)
        self._set_fire_data(fire)

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
            'total_consumption': fire.get('consumption', {}).get('summary',{}).get('total'),
            'total_emissions': fire.get('emissions', {}).get('summary',{}).get('total'),
            'PM2.5': fire.get('emissions', {}).get('summary',{}).get('PM2.5'),
            'num_locations': len(locations),
            'total_area': sum([l['area'] for l in locations]),
            'start': min([aa['start'] for aa in active_areas]),
            'end': max([aa['end'] for aa in active_areas])
        }


    ##
    ## Per Location Data
    ##

    def _set_per_location_data(self, fire):
        self['active_areas'] = []
        for i, aa in enumerate(fire.active_areas):
            # set location ids

            self['active_areas'].append({
                "id": "#{} {} - {}".format(i, aa['start'], aa['end']),
                "start": aa['start'],
                "end": aa['end'],
                'locations': []
            })
            for j, loc in enumerate(aa.locations):
                lat_lng = locationutils.LatLng(loc)
                emissions = self._get_location_emissions(loc)
                timeprofiled_emissions = self._get_location_timeprofiled_emissions(
                    aa, loc, emissions)
                self['active_areas'][-1]['locations'].append({
                    "start": aa["start"],
                    "end": aa["end"],
                    "lat": lat_lng.latitude,
                    "lng": lat_lng.longitude,
                    "area": loc["area"],
                    "id": "#{}/#{} {},{}".format(
                        i, j, lat_lng.latitude, lat_lng.longitude),
                    "fuelbeds": fuelbeds.summarize([self._wrap_loc_in_fire(loc)]),
                    'consumption_by_category': self._get_location_consumption(loc),
                    "emissions": emissions,
                    'timeprofiled_emissions': timeprofiled_emissions,
                    "plumerise": self._get_location_plumerise(loc)
                })

    def _wrap_loc_in_fire(self, loc):
        return models.fires.Fire({
            'activity':[{
                'active_areas':[{
                    'specified_points': [loc]
                }]
            }]
        })

    PHASES = ['flaming', 'smoldering', 'residual']

    def _get_location_consumption(self, loc):
        consumption = defaultdict(lambda: 0.0)
        for fb in loc.get('fuelbeds', []):
            for c in fb.get('consumption', {}):
                for sc in fb['consumption'].get(c, {}):
                    # Each fb['consumption'][c][sc][p] is an array of one value
                    consumption[c] += sum([sum(fb['consumption'][c][sc][p])
                        for p in self.PHASES])
        return consumption


    def _get_location_emissions(self, loc):
        # sum the emissions across all fuelbeds, but keep them separate by phase
        # we want species to be the outer dict and phase the innter
        emissions = {}
        for fb in loc.get('fuelbeds', []):
            for p in self.PHASES:
                for s in fb['emissions'].get(p, {}):
                    emissions[s] = emissions.get(s, {})
                    # fb['emissions'][p][s] is an array of one value
                    emissions[s][p] = (emissions[s].get(p, 0.0)
                        + sum(fb['emissions'][p][s]))
        return emissions

    def _get_location_timeprofiled_emissions(self, aa, loc, emissions):
        tp_emissions = defaultdict(lambda: defaultdict(lambda: 0.0))
        per_species = {}
        for s in emissions:
            for t in sorted(aa.get('timeprofile', {}).keys()):
                d = aa['timeprofile'][t]
                tp_emissions[t][s] += sum([
                    d[p]*emissions[s][p] for p in self.PHASES
                ])
        return tp_emissions

    def _get_location_plumerise(self, loc):
        return [
            {
                't': t,
                'heights': d['heights'],
                'emission_fractions': d['emission_fractions']
            } for t, d in loc.get('plumerise', {}).items()
        ]


    ##
    ## Per Fire Data
    ##

    def _set_fire_data(self, fire):
        self._set_fire_fuelbeds(fire)
        self._set_fire_consumption()
        self._set_fire_timeprofiled_emissions()

    def _set_fire_fuelbeds(self, fire):
        # throw away 'total_area' return value
        self['fuelbeds'] = fuelbeds.summarize([fire])

    def _set_fire_consumption(self):
        # sum the consumption across all fuelbeds and phases, but keep them
        # separate by category
        consumption = defaultdict(lambda: 0.0)
        for aa in self['active_areas']:
            for loc in aa['locations']:
                for c in loc['consumption_by_category']:
                    consumption[c] += loc['consumption_by_category'][c]
        self['consumption_by_category'] = dict(consumption)

    def _set_fire_timeprofiled_emissions(self):
        self['timeprofiled_emissions'] = defaultdict(
            lambda: defaultdict(lambda: 0.0))
        for aa in self['active_areas']:
            for loc in aa['locations']:
                for t, t_dict in loc['timeprofiled_emissions'].items():
                    for s, val in t_dict.items():
                        self['timeprofiled_emissions'][t][s] += val


def summarized_fires_by_id(fires):
    summarized_fires = [SummarizedFire(f) for f in fires]
    return {
        sf['flat_summary']['id']: sf for sf in summarized_fires
    }