from bluesky import models

class SummarizedFire(dict):

    def __init__(self, fire):
        fire = models.fires.Fire(fire)
        locations = fire.locations
        active_areas = fire.active_areas

        self['id'] = fire.get('id')
        self['total_consumption'] = fire.consumption['summary']['total']
        self['total_emissions'] = fire.emissions['summary']['total']
        self['PM2.5'] = fire.emissions['summary']['PM2.5']
        self['num_locations'] = len(locations)
        self['total_area'] = sum([l['area'] for l in locations])
        self['start'] = min([aa['start'] for aa in active_areas])
        self['end'] = min([aa['end'] for aa in active_areas])
