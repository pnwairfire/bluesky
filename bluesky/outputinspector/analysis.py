import pandas as pd

from bluesky import models, locationutils

class SummarizedFire(dict):

    def __init__(self, fire):
        self.fire = models.fires.Fire(fire)

        self.active_areas = self.fire.active_areas
        self.locations = self.fire.locations
        self._set_lat_lng()
        self._set_flat_summary()
        # lazy generate timeprofiles emissions, and memoize
        self._timeprofiled_emissions = None

    def _set_lat_lng(self):
        lat_lngs = [locationutils.LatLng(l) for l in self.locations]

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

    def _set_flat_summary(self):
        self['flat_summary'] = {
            'id': self.fire.get('id'),
            'avg_lat': self['lat_lng']['lat']['avg'],
            'lat': self['lat_lng']['lat']['pretty_str'],
            'avg_lng':  self['lat_lng']['lng']['avg'],
            'lng': self['lat_lng']['lat']['pretty_str'],
            'total_consumption': self.fire.consumption['summary']['total'],
            'total_emissions': self.fire.emissions['summary']['total'],
            'PM2.5': self.fire.emissions['summary']['PM2.5'],
            'num_locations': len(self.locations),
            'total_area': sum([l['area'] for l in self.locations]),
            'start': min([aa['start'] for aa in self.active_areas]),
            'end': max([aa['end'] for aa in self.active_areas])
        }

    def get_timeprofiled_emissions(self):
        if not self._timeprofiled_emissions:
            self._timeprofiled_emissions = []
            for aa in self.fire.active_areas:
                for loc in aa.locations:
                    emissions = self._get_emissions(loc)
                    per_species = {}
                    for s in emissions:
                        per_species[s] = []
                        for t, d in aa.get('timeprofile', {}).items():
                            per_species[s].append({
                                'dt': t,
                                'val': sum([
                                    d[p]*emissions[s][p] for p in self.PHASES
                                ])
                            })
                    if per_species:
                        lat_lng = locationutils.LatLng(loc)
                        self._timeprofiled_emissions.append({
                            # TODO: specify if specifed_point or perimeter?
                            'lat': lat_lng.latitude,
                            'lng': lat_lng.longitude,
                            'area': loc.get('area'),
                            'timeprofiled_emissions': {s: pd.DataFrame(v) for s,v in per_species.items()}
                        })

        return self._timeprofiled_emissions

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
        sf.fire['id']: sf for sf in summarized_fires
    }