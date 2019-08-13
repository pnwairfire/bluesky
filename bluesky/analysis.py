from bluesky import models, locationutils

class SummarizedFire(dict):

    def __init__(self, fire):
        self.fire = models.fires.Fire(fire)

        self.active_areas = self.fire.active_areas
        self.locations = self.fire.locations
        self.set_lat_lng()

        self['id'] = self.fire.get('id')
        self['total_consumption'] = self.fire.consumption['summary']['total']
        self['total_emissions'] = self.fire.emissions['summary']['total']
        self['PM2.5'] = self.fire.emissions['summary']['PM2.5']
        self['num_locations'] = len(self.locations)
        self['total_area'] = sum([l['area'] for l in self.locations])
        self['start'] = min([aa['start'] for aa in self.active_areas])
        self['end'] = max([aa['end'] for aa in self.active_areas])

    def set_lat_lng(self):
        lat_lngs = [locationutils.LatLng(l) for l in self.locations]

        def format_str(mi, ma):
            return "{} to {}".format(mi, ma) if mi != ma else mi

        lats = [ll.latitude for ll in lat_lngs]
        min_lat = min(lats)
        max_lat = max(lats)
        self['lat'] = format_str(min_lat, max_lat)

        lngs = [ll.longitude for ll in lat_lngs]
        min_lng = min(lngs)
        max_lng = max(lngs)
        self['lng'] = format_str(min_lng, max_lng)
