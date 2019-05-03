
REQUIRED_LOCATION_FIELDS = {
    'specified_points': ['lat', 'lng', 'area'],
    'perimeter': ['polygon']
}

INVALID_LOCATION_MSGS = {
    k: "Each active area {} must define '{}'".format(
        k.replace('_', ' ').rstrip('s'),
        "', '".join(REQUIRED_LOCATION_FIELDS[k]))
    for k in REQUIRED_LOCATION_FIELDS
}

class ActiveArea(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: call locations to run validation?
        #self.locations


    MISSING_LOCATION_INFO_MSG = ("Each active area must contain "
        "'specified_points' or 'perimeter'")

    @property
    def locations(self):
        """Returns the specified_points or perimeter polygon as list.

        This method validates data and casts areas to float every time it
        is called, in case fire activity data is made invalid mid-run
        (which should only be possibly if a user imports the bluesky package
        instead of running 'bsp')

        Note that perimeter 'area' does not need to be defined, since
        this method will be called before fuelbeds, which fills in perimeter
        area if not already defined.
        """
        if self.get('specified_points'):
            return self._validate_locations('specified_points')

        elif self.get('perimeter'):
            return self._validate_locations('perimeter')

        else:
            raise ValueError(self.MISSING_LOCATION_INFO_MSG)

    def _validate_locations(self, key):
        locations = [self[key]] if key == 'perimeter' else self[key]

        if any([any([not p.get(f) for f in REQUIRED_LOCATION_FIELDS[key]])
                for p in locations]):
            raise ValueError(INVALID_LOCATION_MSGS[key])

        # cast any string areas to float
        for loc in locations:
            if hasattr(loc.get('area'), 'capitalize'):
                loc['area'] = float(loc['area'])

        return locations


    MISSING_OR_INVALID_AREA_FOR_SPECIFIED_POINT = (
        "Missing or invalid area for specified point")
    MISSING_OR_INVALID_AREA_FOR_PERIMIETER = (
        "Missing or invalid area for active area perimeter")

    @property
    def total_area(self):
        """Returns the cumulative area of all specified_points, if defined.
        or else the perimeter area.

        Note that, by the time that this method is called, if there are
        not specified points, then the perimeter must have area defined.
        """

        if 'specified_points' in self:
            try:
                area_vals = [float(p.get('area'))
                    for p in self['specified_points']]
            except:
                raise ValueError(self.MISSING_OR_INVALID_AREA_FOR_SPECIFIED_POINT)
            return sum(area_vals)

        elif 'perimeter' in self:
            try:
                return float(self['perimeter'].get('area'))
            except:
                raise ValueError(self.MISSING_OR_INVALID_AREA_FOR_PERIMIETER)
            return self['perimeter']['area']

        else:
            raise ValueError(self.MISSING_LOCATION_INFO_FOR_ACTIVE_AREA)

class ActivityCollection(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for i in range(len(self.get('active_areas', []))):
            self['active_areas'][i] = ActiveArea(self['active_areas'][i])

    @property
    def active_areas(self):
        return self.get('active_areas', [])
