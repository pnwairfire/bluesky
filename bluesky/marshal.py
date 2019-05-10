"""bluesky.marshal"""

__author__ = "Joel Dubowy"


import copy

from bluesky.models.fires import Fire


__all__ = [
    "Blueskyv4_0To4_1"
]


EXTRA_LOC_FIELDS = (
    'fuelbeds',
    'fuelbeds_total_accounted_for_pct',
    'localmet',
    'plumerise'
    # TODO: add fields
)

TO_COPY_UP = {
    'consumption',
    'heat',
    'emissions',
    'emissions_details',
}

class Blueskyv4_0To4_1(object):

    def marshal(self, fires):
        return [self.marshal_fire(fire) for fire in fires]

    def marshal_fire(self, fire):
        # TODO: break this method up into multiple methods
        fire = copy.deepcopy(fire)

        activity = fire.pop('activity', None) or fire.pop('growth', [])
        fire['activity'] = []
        for old_a in activity:
            loc = old_a.pop('location', {})
            lat = loc.pop('latitude', None)
            lng = loc.pop('longitude', None)
            area = loc.pop('area', None)
            geojson = loc.pop('geojson', None)

            aa_template = dict(loc)
            new_a = {'active_areas': []}

            loc_template = {}
            for k in EXTRA_LOC_FIELDS:
                val = old_a.pop(k, None)
                if val:
                    loc_template[k] = val

            for k in TO_COPY_UP:
                val = old_a.pop(k, None)
                if val:
                    loc_template[k] = val
                    new_a[k] = val
                    aa_template[k] = val

            aa_template.update(**old_a)

            if lat is not None and lng is not None:
                aa = copy.deepcopy(aa_template)
                aa["specified_points"] = [
                    dict(loc_template, lat=lat, lng=lng, area=area)
                ]
                new_a["active_areas"].append(aa)

            elif geojson:
                if geojson['type'] == 'Polygon':
                    aa = copy.deepcopy(aa_template)
                    aa["perimeter"] = dict(loc_template,
                        polygon=geojson['coordinates'][0], area=area)
                    new_a["active_areas"].append(aa)

                elif geojson['type'] == 'MultiPolygon':
                    for p in geojson['coordinates']:
                        aa = copy.deepcopy(aa_template)
                        aa["perimeter"] = dict(loc_template,
                            polygon=p[0], area=area)
                        new_a['active_areas'].append(aa)

                elif geojson['type'] == 'MultiPoint' and area:
                    aa = copy.deepcopy(aa_template)
                    num_points = len(geojson['coordinates'])
                    aa["specified_points"] = [
                        dict(loc_template,lat=p[1],lng=p[0],
                            area=area / num_points)
                        for p in geojson['coordinates']
                    ]
                    new_a['active_areas'].append(aa)

                elif geojson['type'] == 'Point' and area:
                    aa = copy.deepcopy(aa_template)
                    aa["specified_points"] = [
                        dict(loc_template,lat=geojson['coordinates'][1],
                            lng=geojson['coordinates'][0], area=area)
                    ]
                    new_a['active_areas'].append(aa)

                else:
                    raise ValueError("Can't convert fire: %s", fire)

            else:
                raise ValueError("Can't convert fire: %s", fire)

            fire['activity'].append(new_a)

        return Fire(fire)
