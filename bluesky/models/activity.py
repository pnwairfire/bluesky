
class ActiveArea(dict):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # TODO: call locations to run validation?
        #self.locations

    POINT_FIELDS = ['lat', 'lng', 'area']
    INVALID_SPECIFIED_POINT_MSG = ("Each point in an active area's"
        " specified_points must have fields '{}'".format(POINT_FIELDS))
    INVALID_PERIMETER_MSG = "An active area's perimeter must have field 'polygon"
    MISSING_LOCATION_INFO_MSG = ("Each active area must contain "
        "'specified_points' or 'perimeter'")

    @property
    def locations(self):
        """Returns the specified_points or perimeter polygon as list.

        validates every time method is called, in case fire activity
        data is made invalid mid-run (which should only be possibly
        if user imports the bluesky package instead of running 'bsp')

        Note that perimeter AREA does not need to be defined, sinte
        this method will be called before fuelbeds, and perimeter
        area is determined from fuelbeds if not already defined.
        """
        if self.get('specified_points'):
            if any([any([not p.get(f) for f in self.POINT_FIELDS])
                    for p in self['specified_points']]):
                raise ValueError(self.INVALID_SPECIFIED_POINT_MSG)
            return self['specified_points']

        elif self.get('perimeter'):
            if not self['perimeter'].get('polygon'):
                raise ValueError(self.INVALID_PERIMETER_MSG)
            return [self['perimeter']]

        else:
            raise ValueError(self.MISSING_LOCATION_INFO_MSG)

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
