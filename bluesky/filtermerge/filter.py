"""bluesky.filtermerge.filter"""

__author__ = "Joel Dubowy"

import datetime
import logging

from bluesky.config import Config
from bluesky.datetimeutils import to_datetime, parse_utc_offset
from bluesky.locationutils import LatLng

from . import FiresActionBase


class FireActivityFilter(FiresActionBase):
    """Class for filtering fire activity windows by various criteria.

    Note: The logic in this class is organized as a saparate class primarily
    for maintainability, testibility, and readability.  Some of it was
    originally in the FiresManager class.
    """

    def __init__(self, fires_manager, fire_class):
        """Constructor

        args:
         - fires_manager -- FiresManager object whose fires are to be merged
         - fire_class -- Fire class to instantiate new fire objects
        """
        super(FireActivityFilter, self).__init__(fires_manager, fire_class)
        self._filter_config = Config().get('filter')
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

    SPECIFY_INCLUSION_OR_EXCLUSION_LIST_MSG = "Specify 'include' or 'exclude' - not both"
    SPECIFY_FILTER_FIELD_MSG = "Specify field to filter on"
    def _get_filter(self, **kwargs):
        inclusion_list = kwargs.get('include')
        exclusion_list = kwargs.get('exclude')
        if (not inclusion_list and not exclusion_list) or (inclusion_list and exclusion_list):
            raise self.FilterError(self.SPECIFY_INCLUSION_OR_EXCLUSION_LIST_MSG)
        filter_field = kwargs.get('filter_field')
        if not filter_field:
            # This will never happen if called internally
            raise self.FilterError(self.SPECIFY_FILTER_FIELD_MSG)

        def _filter(fire, active_area):
            v = active_area.get(filter_field)
            if inclusion_list:
                return not v or v not in inclusion_list
            else:
                return v and v in exclusion_list

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
                total_active_area = active_area.total_area
            except:
                self._fail_fire(fire, self.MISSING_ACTIVITY_AREA_MSG)

            if total_active_area < 0.0:
                self._fail_fire(fire, self.NEGATIVE_ACTIVITY_AREA_MSG)

            return ((min_area is not None and total_active_area < min_area) or
                (max_area is not None and total_active_area > max_area))

        return _filter



    SPECIFY_TIME_START_AND_OR_END_MSG = "Specify start and/or end to filter by time"
    INVALID_TIME_START_OR_END_VAL = "Invalid value for time filter config option '{}'"
    INVALID_START_AFTER_END = ("Start must be before end if both are specified"
        " for time fileter")

    def _get_time_filter(self, **kwargs):
        """Returns function that checks if fire activity window is after
        specified start time and/or before specified end time.
        """
        s = kwargs.get('start')
        e = kwargs.get('end')
        if not s and not e:
            raise self.FilterError(self.SPECIFY_TIME_START_AND_OR_END_MSG)

        def _parse(v, key):
            try:
                is_local = hasattr(v, 'endswith') and v.endswith('L')
                return (
                    to_datetime(v.rstrip('L') if hasattr(v, 'rstrip') else v),
                    is_local
                )
            except:
                raise self.FilterError(
                    self.INVALID_TIME_START_OR_END_VAL.format(key))

        s, s_is_local = _parse(s, 'start')
        e, e_is_local = _parse(e, 'end')

        if s and e and s > e:
            raise self.FilterError(self.INVALID_START_AFTER_END)

        def _filter(fire, active_area):
            if not isinstance(active_area, dict):
                self._fail_fire(fire, self.MISSING_FIRE_LOCATION_INFO_MSG)
            elif not active_area.get('start') or not active_area.get('end'):
                self._fail_fire(fire, self.MISSING_FIRE_LOCATION_INFO_MSG)

            utc_offset = datetime.timedelta(hours=parse_utc_offset(
                active_area.get('utc_offset') or 0))

            aa_s = to_datetime(active_area['start'])
            # check if e_is_local, since we're comparing aa_s against e
            if not e_is_local:
                aa_s = aa_s - utc_offset

            aa_e = to_datetime(active_area['end'])
            # same thing, but s_is_local
            if not s_is_local:
                aa_e = aa_e - utc_offset

            # note that this filters if aa's start/end matches cutoff
            # (e.g. if aa's start and filter's end are both 2019-01-01T00:00:00)
            return (s and aa_e <= s) or (e and aa_s >= e)

        return _filter
