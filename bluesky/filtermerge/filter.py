"""bluesky.filtermerge.filter"""

__author__ = "Joel Dubowy"

import logging

from bluesky.config import Config
from bluesky.locationutils import LatLng, get_total_active_area

from . import FiresActionBase


class FireActivityFilter(FiresActionBase):
    """Class for filtering fire activity windows by various criteria.

    Note: The logic in this class is organized as a saparate class primarily
    for maintainability, testibility, and readability.  Some of it was
    originally in the FiresManager class.
    """

    def __init__(self, fires_manager):
        """Constructor

        args:
         - fires_manager -- FiresManager object whose fires are to be merged
        """
        super(FireActivityFilter, self).__init__(fires_manager)
        self._filter_config = Config.get('filter')
        self._filter_fields = set(self._filter_config.keys()) - set(['skip_failures'])
        if not self._filter_fields:
            if not self._skip_failures:
                raise self.FilterError(self.NO_FILTERS_MSG)
            # else, just log and return
            logging.warning(self.NO_FILTERS_MSG)


    ACTION = 'filter'
    @property
    def _action(self):
        return self.ACTION

    class FilterError(Exception):
        pass
    @property
    def _error_class(self):
        return self.FilterError

    ##
    ## Public API
    ##

    NO_FILTERS_MSG = "No filters specified"
    def filter(self):
        """Runs all secified filtered
        """
        for filter_field in self._filter_fields:
            logging.debug('About to run %s filter', filter_field)

            # get filter function
            try:
                filter_func = self._get_filter_func(filter_field)

            except self.FilterError as e:
                if self._skip_failures:
                    logging.warning("Failed to initialize %s filter: %s",
                        filter_field, e)
                    continue
                else:
                    raise

            # run filter
            self._filter(filter_func)
            logging.info("Number of fires after running %s filter: %d",
                filter_field, self._fires_manager.num_fires)

    INVALID_FILTER_MSG = "Invalid filter"
    MISSING_FILTER_CONFIG_MSG = "Specify config for each filter"
    def _get_filter_func(self, filter_field):
        """Filters by specified field

        args
         - filter_field -- field to filter by (e.g. 'country')
        """
        filter_getter = getattr(self, '_get_{}_filter'.format(filter_field),
            self._get_filter)
        if not filter_getter:
            self._fail_or_skip(self.MISSING_FILTER_CONFIG_MSG)

        kwargs = self._filter_config.get(filter_field)
        if not kwargs:
            self._fail_or_skip(self.MISSING_FILTER_CONFIG_MSG)

        kwargs.update(filter_field=filter_field)
        return filter_getter(**kwargs)

    def _filter(self, filter_func):
        """Filter by given filter func

        args:
         - filter_func -- function that takes fire and active area object
            and returns boolean value indicating whether or not to remove
            active area object.
        """
        for fire in self._fires_manager.fires:
            i = 0
            while i < len(fire.get('activity', [])):
                j = 0
                while j < len(fire['activity'][i].get('active_areas', [])):
                    try:
                        if filter_func(fire, fire['activity'][i]['active_areas'][j]):
                            fire['activity'][i]['active_areas'].pop(j)
                            logging.debug('Filtered fire %s (%s)', fire.id,
                                fire._private_id)
                            # Note: if that was the last active area, then
                            #    `j` must equal zero, and while loop will
                            #    terminate
                        else:
                            j += 1

                    except self.FilterError as e:
                        if self._skip_failures:
                            j += 1
                            # str(e) is already detailed
                            logging.warning(str(e))
                            continue
                        else:
                            raise

                if len(fire['activity'][i].get('active_areas', [])) == 0:
                    fire['activity'].pop(i)

                else:
                    i += 1

            if len(fire.get('activity', [])) == 0:
                self._remove_fire(fire)

    def _remove_fire(self, fire):
        """Removes fire from fires manager's `fires` list, and adds it
        to `filtered_fires`

        args
         - fire -- fire to remove from active set
        """
        self._fires_manager.remove_fire(fire)
        if self._fires_manager.filtered_fires is None:
            self._fires_manager.filtered_fires  = []
        # TDOO: add reason for filtering (specify at least filed)
        self._fires_manager.filtered_fires.append(fire)

    ##
    ## Unterlying filter methods
    ##

    SPECIFY_WHITELIST_OR_BLACKLIST_MSG = "Specify whitelist or blacklist - not both"
    SPECIFY_FILTER_FIELD_MSG = "Specify field to filter on"
    def _get_filter(self, **kwargs):
        whitelist = kwargs.get('whitelist')
        blacklist = kwargs.get('blacklist')
        if (not whitelist and not blacklist) or (whitelist and blacklist):
            raise self.FilterError(self.SPECIFY_WHITELIST_OR_BLACKLIST_MSG)
        filter_field = kwargs.get('filter_field')
        if not filter_field:
            # This will never happen if called internally
            raise self.FilterError(self.SPECIFY_FILTER_FIELD_MSG)

        def _filter(fire, active_area):
            v = active_area.get(filter_field)
            if whitelist:
                return not v or v not in whitelist
            else:
                return v and v in blacklist

        return _filter


    SPECIFY_BOUNDARY_MSG = "Specify boundary to filter by location"
    INVALID_BOUNDARY_FIELDS_MSG = ("Filter boundary must specify"
        " 'ne' and 'sw', which each must have 'lat' and 'lng'")
    INVALID_BOUNDARY_MSG = "Invalid boundary for filtering"
    MISSING_FIRE_LOCATION_INFO_MSG = ("Fire active areas must"
        " have location information to be filtered by location")
    def _get_location_filter(self, **kwargs):
        """Returns function that checks if fire activity window is within
        boundary, which should be of the form:

            {
                "ne": {
                    "lat": 45.25,
                    "lng": -106.5
                },
                "sw": {
                    "lat": 27.75,
                    "lng": -131.5
                }
            }

        Note: this function does not support boundaries spanning the
        international date line.  (i.e. NE lng > SW lng)
        """
        b = kwargs.get('boundary')
        if not b:
            raise self.FilterError(self.SPECIFY_BOUNDARY_MSG)
        elif (set(b.keys()) != set(["ne", "sw"]) or
                any([set(b[k].keys()) != set(["lat", "lng"])
                    for k in ["ne", "sw"]])):
            raise self.FilterError(self.INVALID_BOUNDARY_FIELDS_MSG)
        elif (any([abs(b[k]['lat']) > 90.0 for k in ['ne','sw']]) or
                any([abs(b[k]['lng']) > 180.0 for k in ['ne','sw']]) or
                any([b['ne'][k] < b['sw'][k] for k in ['lat','lng']])):
            raise self.FilterError(self.INVALID_BOUNDARY_MSG)

        def _filter(fire, active_area):
            if not isinstance(active_area, dict):
                self._fail_fire(fire, self.MISSING_FIRE_LOCATION_INFO_MSG)
            try:
                latlng = LatLng(active_area)
                lat = latlng.latitude
                lng = latlng.longitude
            except ValueError as e:
                self._fail_fire(fire, self.MISSING_FIRE_LOCATION_INFO_MSG)
            if not lat or not lng:
                self._fail_fire(fire, self.MISSING_FIRE_LOCATION_INFO_MSG)

            return (lat < b['sw']['lat'] or lat > b['ne']['lat'] or
                lng < b['sw']['lng'] or lng > b['ne']['lng'])

        return _filter

    SPECIFY_MIN_OR_MAX_MSG = "Specify min and/or max area for filtering"
    INVALID_MIN_MAX_MUST_BE_POS_MSG = "Min and max areas must be positive for filtering"
    INVALID_MIN_MUST_BE_LTE_MAX_MSG = "Min area must be LTE max if both are specified"
    MISSING_ACTIVITY_AREA_MSG = "Fire active area must have area information to be filtered by area"
    NEGATIVE_ACTIVITY_AREA_MSG = "Fire active area's total can't be negative"
    def _get_area_filter(self, **kwargs):
        """Returns funciton that checks if a fire is smaller than some
        max threshold and/or larger than some min threshold.
        """
        min_area = kwargs.get('min')
        max_area = kwargs.get('max')
        if min_area is None and max_area is None:
            raise self.FilterError(self.SPECIFY_MIN_OR_MAX_MSG)
        elif ((min_area is not None and min_area < 0.0) or
                (max_area is not None and max_area < 0.0)):
            raise self.FilterError(self.INVALID_MIN_MAX_MUST_BE_POS_MSG)
        elif (min_area is not None and max_area is not None and
                min_area > max_area):
            raise self.FilterError(self.INVALID_MIN_MUST_BE_LTE_MAX_MSG)

        def _filter(fire, active_area):
            try:
                total_area = get_total_active_area(active_area)
            except:
                self._fail_fire(fire, self.MISSING_ACTIVITY_AREA_MSG)

            if total_active_area < 0.0:
                self._fail_fire(fire, self.NEGATIVE_ACTIVITY_AREA_MSG)

            return ((min_area is not None and total_active_area < min_area) or
                (max_area is not None and total_active_area > max_area))

        return _filter
