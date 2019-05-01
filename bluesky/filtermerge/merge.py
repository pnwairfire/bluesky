"""bluesky.filtermerge.merge"""

__author__ = "Joel Dubowy"

import logging

from . import FiresActionBase

class FiresMerger(FiresActionBase):
    """Class for merging fires with the same id.

    e.g. For fires that have a separate listing for each day in their duration.

    Note: The logic in this class is organized as a saparate class primarily
    for maintainability, testibility, and readability.  It was originally in
    the FiresManager class.
    """

    ACTION = 'merge'
    @property
    def _action(self):
        return self.ACTION

    class MergeError(Exception):
        pass
    @property
    def _error_class(self):
        return self.MergeError

    ##
    ## Public API
    ##

    def merge(self):
        """Merges fires that have the same id.
        """
        for fire_id in list(self._fires_manager._fires.keys()):
            if len(self._fires_manager._fires[fire_id]) > 1:
                logging.debug("merging records for fire %s ", fire_id)
                self._merge_fire_id(fire_id)

    ##
    ## Merge Methods
    ##

    def _merge_fire_id(self, fire_id):
        """Actually does the merging of fires with a given id

        args:
         - fire_id -- common fire id

        For simplicity, the logic iterates once through the fires, in
        order. This might miss potential merges (e.g. if all but the
        first fire have the same location), but those should be
        edge cases.  So, it seems that it would be overengineering and not
        worth the hit to performance to check every pair of fires for
        mergeability.

        TODO: refactor inner loop logic into submethods
        """
        combined_fire = None
        for fire in self._fires_manager._fires[fire_id]:
            try:
                # TODO: iterate through and call all methods starting
                #   with '_check_'; would need to change _check_keys'
                #   signature to match the others
                self._check_keys(fire)
                self._check_activity_windows(fire, combined_fire)
                self._check_event_of(fire, combined_fire)
                self._check_fire_and_fuel_types(fire, combined_fire)

                combined_fire = self._merge_into_combined_fire(fire,
                    combined_fire)

            except FiresMerger.MergeError as e:
                if not self._skip_failures:
                    if combined_fire:
                        # add back what was merge in progress
                        self._fires_manager.add_fire(combined_fire)
                    raise ValueError(str(e))
                # else, just log str(e) (which is detailed enough)
                logging.warning(str(e))

        if combined_fire:
            # add_fire will take care of creating new list
            # and adding fire id in the case where all fires
            # were combined and thus all removed
            self._fires_manager.add_fire(combined_fire)


    def _merge_into_combined_fire(self, fire, combined_fire):
        """Merges fires into in-progress combined fire

        args:
         - fire -- fire to merge
         - combined_fire -- in-progress combined fire (which could be None)
        """
        if not combined_fire:
            # We need to instantiate a dict from fire in order to deepcopy it.
            # We need to deepcopy so that that modifications to
            # new_combined_fire don't modify fire
            new_combined_fire = Fire(copy.deepcopy(dict(fire)))
            self._fires_manager.remove_fire(fire)

        else:
            # See note, above, regarding instantiating dict and then deep copying
            new_combined_fire = Fire(copy.deepcopy(dict(combined_fire)))
            try:
                # merge activity; remember, at this point, activity will be
                # defined for none or all of the fires to be merged
                if new_combined_fire.get('activity'):
                    new_combined_fire.activity.extend(copy.deepcopy(fire.activity))
                    new_combined_fire.activity.sort(key=lambda e: e['start'])

                # TODO: merge anything else?

                # if remove_fire fails, combined_fire won't be updated
                self._fires_manager.remove_fire(fire)

            except Exception as e:
                self._fail_fire(fire, e)

        return new_combined_fire

    ##
    ## Validation / Check Methods
    ##

    # TODO: maybe eventually be able to merge post-consumption, emissions,
    #   etc., but for now only support merging just-ingested fire data
    ALL_MERGEABLE_FIELDS = set(
        ["id", "event_of", "type", "fuel_type", "activity"])
    INVALID_KEYS_MSG =  "invalid data set"
    def _check_keys(self, fire):
        keys = set(fire.keys())
        if not keys.issubset(self.ALL_MERGEABLE_FIELDS):
            self._fail_fire(fire, self.INVALID_KEYS_MSG)

    ACTIVITY_FOR_BOTH_OR_NONE_MSG = ("activity windows must be defined for both "
        "fires or neither in order to merge")
    OVERLAPPING_ACTIVITY_WINDOWS = "activity windows overlap"
    def _check_activity_windows(self, fire, combined_fire):
        """Makes sure activity windows are defined for all or none,
        and if defined, make sure they don't overlap

        Ultimately, overlapping activity windows could be handled,
        but at this point it would be overengineering.
        """
        if combined_fire and (
                bool(combined_fire.get('activity')) != bool(fire.get('activity'))):
            self._fail_fire(fire, self.ACTIVITY_FOR_BOTH_OR_NONE_MSG)

        # TODO: check for overlaps
        # TODO: additionally, take into account time zones when checking
        #    for overlaps

    EVENT_MISMATCH_MSG = "fire event ids don't match"
    def _check_event_of(self, fire, combined_fire):
        """Makes sure event ids, if both defined, are the same
        """
        c_event_id = combined_fire and combined_fire.get(
            'event_of', {}).get('id')
        f_event_id = fire.get('event_of', {}).get('id')
        if c_event_id and f_event_id and c_event_id != f_event_id:
            self._fail_fire(fire, self.EVENT_MISMATCH_MSG)

    FIRE_TYPE_MISMATCH_MSG = "Fire types don't match"
    FUEL_TYPE_MISMATCH_MSG = "Fuel types don't match"
    def _check_fire_and_fuel_types(self, fire, combined_fire):
        """Makes sure fire and fuel types are the same
        """
        if combined_fire:
            if fire.type != combined_fire.type:
                self._fail_fire(fire, self.FIRE_TYPE_MISMATCH_MSG)
            if fire.fuel_type != combined_fire.fuel_type:
                self._fail_fire(fire, self.FUEL_TYPE_MISMATCH_MSG)
