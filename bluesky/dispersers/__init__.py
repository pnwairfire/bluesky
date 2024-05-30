"""bluesky.dispersers

TODO: Move this package into it's own repo. One thing that would need to be
done first is to remove the dependence on bluesky.models.fires.Fire.
This would be fairly easy, since Fire objects are for the most part dicts.
Attr access of top level keys would need to be replaced with direct key
access, and the logic in Fire.latitude and Fire.longitude would need to be
moved into hysplit.py.
"""

__author__ = "Joel Dubowy"

import abc
import itertools
import logging
import math
import os
import shutil
from datetime import timedelta

from pyairfire import osutils
from afdatetime import parsing as datetime_parsing

from bluesky import datautils, locationutils
from bluesky.config import Config
from bluesky.datetimeutils import parse_utc_offset
from bluesky.models.fires import Fire
from . import firemerge


# Note: HYSPLIT can accept concentrations in any units, but for
# consistency with CALPUFF and other dispersion models, we convert to
# grams in the emissions file.
GRAMS_PER_TON = 907184.74
SECONDS_PER_HR = 60 * 60
TONS_PER_HR_TO_GRAMS_PER_SEC = GRAMS_PER_TON / SECONDS_PER_HR
BTU_TO_MW = 3414425.94972     # Btu to MW

# Conversion factor for fire size
SQUARE_METERS_PER_ACRE = 4046.8726
PHASES = ['flaming', 'smoldering', 'residual']

class SkipLocationError(Exception):
    pass

class DispersionBase(object, metaclass=abc.ABCMeta):

    # 'BINARIES' dict should be defined by each subclass which depend on
    # external binaries
    BINARIES = {}


    def __init__(self, met_info):
        self._model = self.__class__.__module__.split('.')[-2]
        self._log_config()

        # TODO: iterate through self.BINARIES.values() making sure each
        #   exists (though maybe only log warning if doesn't exist, since
        #   they might not all be called for each run
        # TODO: define and call method (which should rely on constant defined
        #   in model-specific classes) which makes sure all required config
        #   options are defined

    def _log_config(self):
        # TODO: bail if logging level is less than DEBUG (to avoid list and
        #   set operations)
        _c = Config().get('dispersion', self._model)
        for c in sorted(_c.keys()):
            logging.debug('Dispersion config setting - %s = %s', c, _c[c])

    def config(self, *keys, **kwargs):
        return Config().get('dispersion', self._model, *keys, **kwargs)

    def run(self, fires_manager, start, num_hours, output_dir, working_dir=None):
        """Runs dispersion model (e.g. hysplit)

        args:
         - fires_manager - FiresManager object
         - start - model run start hour
         - num_hours - number of hours in model run
         - output_dir - directory to contain output

        kwargs:
         - working_dir -- working directory to write input files and output
            files (before they're copied over to final output directory);
            if not specified, a temp directory is created
        """
        logging.info("Running %s", self.__class__.__name__)

        self._warnings = []

        if start.minute or start.second or start.microsecond:
            raise ValueError("Dispersion start time must be on the hour.")
        if type(num_hours) != int:
            raise ValueError("Dispersion num_hours must be an integer.")
        self._model_start = start
        self._num_hours = num_hours

        self._run_output_dir = output_dir # already created

        self._working_dir = working_dir and os.path.abspath(working_dir)
        # osutils.create_working_dir will create working dir if necessary

        counts = {'fires': len(fires_manager.fires)}
        self._set_fire_data(fires_manager.fires)
        counts['locations'] = len(self._fires)

        # TODO: only merge fires if hysplit, or make it configurable ???
        self._fires = firemerge.FireMerger().merge(self._fires)
        # TODO: should we pop 'end' from each fire object, since it's
        #   only used in _merge_fires logic?
        counts['distinct_locations'] = len(self._fires)

        pm_config = Config().get('dispersion', 'plume_merge')
        if pm_config:
            # TODO: make sure pm_config boundary includes all of disperion
            #   boundary, and raise BlueSkyConfigurationError if not?
            self._fires = firemerge.PlumeMerger(pm_config).merge(self._fires)

        counts['plumes'] = len(self._fires)
        notes = "Plumes to be modeled by dispersion"
        fires_manager.log_status('Good', 'dispersion', 'Continue',
            number_of_locations=counts['plumes'], notes=notes)

        delete_if_no_error = Config().get(
            'dispersion', 'delete_working_dir_if_no_error')
        with osutils.create_working_dir(working_dir=self._working_dir,
                delete_if_no_error=delete_if_no_error) as wdir:
            r = self._run(wdir)

        r["counts"] = counts
        r["output"].update({
            "directory": self._run_output_dir,
            "start_time": self._model_start.isoformat(),
            "num_hours": self._num_hours
        })
        if self._working_dir:
            r["output"]["working_dir"] = self._working_dir
        if self._warnings:
            r["warnings"] = self._warnings

        return r

    @abc.abstractmethod
    def _required_activity_fields(self):
        pass

    @abc.abstractmethod
    def _run(self, wdir):
        """Underlying run method to be implemented by subclasses
        """
        pass

    def _record_warning(self, msg, **kwargs):
        self._warnings.append(dict(message=msg, **kwargs))

    MISSING_PLUMERISE_HOUR = dict(
        heights=[0.0] * 21, # everthing emitted at the ground
        emission_fractions=[0.05] * 20,
        smolder_fraction=0.0
    )
    MISSING_TIMEPROFILE_HOUR = dict({p: 0.0 for p in PHASES}, area_fraction=0.0)

    SPECIES = ('PM2.5', 'CO')

    def _set_fire_data(self, fires):
        self._fires = []

        # TODO: aggreagating over all fires (if psossible)
        #  use self.model_start and self.model_end
        #  as disperion time window, and then look at
        #  activity window(s) of each fire to fill in emissions for each
        #  fire spanning hysplit time window
        # TODO: determine set of arl fires by aggregating arl files
        #  specified per activity per fire, or expect global arl files
        #  specifications?  (if aggregating over fires, make sure they're
        #  conistent with met domain; if not, raise exception or run them
        #  separately...raising exception would be easier for now)
        # Make sure met files span dispersion time window
        activity_fields = self._required_activity_fields() + ('fuelbeds', )
        for fire in fires:
            try:
                # make sure it has locations, but then iterate through
                # active areas and then locations
                if not fire.locations:
                    raise ValueError(
                        "Missing fire activity data required for computing dispersion")

                loc_num = 0
                for aa in fire.active_areas:
                    utc_offset = self._get_utc_offset(aa)
                    for loc in aa.locations:
                        try:
                            self._add_location(fire, aa, loc,
                                activity_fields, utc_offset, loc_num)
                            loc_num += 1

                        except SkipLocationError:
                            continue

            except:
                if self.config('skip_invalid_fires'):
                    continue
                else:
                    raise

        # Note: even if self._fires is emtpy, we don't want to abort (like
        # we used to do), since we want output even if it's blank

    ## Creating fires out of locations

    def _add_location(self, fire, aa, loc, activity_fields, utc_offset, loc_num):
        if any([not loc.get(f) for f in activity_fields]):
            raise ValueError("Each active area must have {} in "
                "order to compute {} dispersion".format(
                ','.join(activity_fields), self.__class__.__name__))
        if any([not fb.get('emissions') for fb in loc['fuelbeds']]):
            raise ValueError(
                "Missing emissions data required for computing dispersion")

        heat = self._get_heat(fire, aa, loc)
        plumerise, timeprofile = self._get_plumerise_and_timeprofile(
            loc, utc_offset)
        emissions = self._get_emissions(loc)
        timeprofiled_emissions = self._get_timeprofiled_emissions(
            timeprofile, emissions)
        timeprofiled_area = {dt: e.get('area_fraction') * loc['area'] for dt,e in timeprofile.items()}

        # consumption = datautils.sum_nested_data(
        #     [fb.get("consumption", {}) for fb in a['fuelbeds']], 'summary', 'total')
        consumption = loc['consumption']['summary']

        latlng = locationutils.LatLng(loc)

        f = Fire(
            id="{}-{}".format(fire.id, loc_num),
            # See note above, in _merge_two_fires, about why
            # original_fire_ids is a set instead of scalar
            original_fire_ids=set([fire.id]),
            meta=fire.get('meta', {}),
            start=datetime_parsing.parse(aa['start']),
            end=datetime_parsing.parse(aa['end']),
            area=loc['area'],
            latitude=latlng.latitude,
            longitude=latlng.longitude,
            utc_offset=utc_offset,
            plumerise=plumerise,
            timeprofiled_emissions=timeprofiled_emissions,
            timeprofiled_area=timeprofiled_area,
            consumption=consumption
        )
        if heat:
            f['heat'] = heat
        self._fires.append(f)

    def _get_plumerise_and_timeprofile(self, loc, utc_offset):
        # TODO: only include plumerise and timeprofile keys within model run
        # time window; and somehow fill in gaps (is this possible?)
        all_plumerise = loc.get('plumerise', {})
        all_timeprofile = loc.get('timeprofile', {})
        plumerise = {}
        timeprofile = {}
        for i in range(self._num_hours):
            local_dt = self._model_start + timedelta(hours=(i + utc_offset))
            # TODO: will all_plumerise and all_timeprofile always
            #    have string value keys
            local_dt = local_dt.strftime('%Y-%m-%dT%H:%M:%S')
            plumerise[local_dt] = all_plumerise.get(local_dt) or self.MISSING_PLUMERISE_HOUR
            timeprofile[local_dt] = all_timeprofile.get(local_dt) or self.MISSING_TIMEPROFILE_HOUR

        return plumerise, timeprofile

    def _get_emissions(self, loc):
        # sum the emissions across all fuelbeds, but keep them separate by phase
        emissions = {p: {} for p in PHASES}
        for fb in loc['fuelbeds']:
            for p in PHASES:
                for s in fb['emissions'][p]:
                    emissions[p][s] = (emissions[p].get(s, 0.0)
                        + sum(fb['emissions'][p][s]))
        return emissions

    def _get_timeprofiled_emissions(self, timeprofile, emissions):
        timeprofiled_emissions = {}
        for dt in timeprofile:
            timeprofiled_emissions[dt] = {}
            for e in self.SPECIES:
                timeprofiled_emissions[dt][e] = sum([
                    timeprofile[dt][p] * emissions[p].get(e, 0.0)
                        for p in PHASES
                ])
        return timeprofiled_emissions


    def _get_heat(self, fire, aa, loc):
        # TDOO: handle case where heat is defined by phase, but not total
        #   (just make sure each phase is defined, and set total to sum)
        heat = None
        heat_values = list(itertools.chain.from_iterable(
            [fb.get('heat', {}).get('total', [None]) for fb in loc['fuelbeds']]))
        if not any([v is None for v in heat_values]):
            heat = sum(heat_values)
            # I'm not sure why we continue if heat is not defined,
            # but skip the active area if it's less than 1.0e-6
            # This came from the BSF code. Maybe we should
            # just set to None if it's less than 1.0e-6 ?
            if  heat < 1.0e-6:
                logging.debug("Fire %s activity window %s - %s has "
                    "less than 1.0e-6 total heat; skip...",
                    fire.id, aa['start'], aa['end'])
                raise SkipLocationError("Heat to low")

        # else, just forget about computing heat
        return heat

    def _get_utc_offset(self, aa):
        utc_offset = aa.get('utc_offset')
        utc_offset = parse_utc_offset(utc_offset) if utc_offset else 0.0
        # round utc_offset offset down to the nearest whole hour (e.g. -3.5 -> -4),
        # since we use it for referencing timeprofile and plumerise data, which
        # have whole hour keys.  It's not used for anything else.
        utc_offset = math.floor(utc_offset)
        return utc_offset


    def _convert_keys_to_datetime(self, d):
        return { datetime_parsing.parse(k): v for k, v in d.items() }


    def _archive_file(self, filename, src_dir=None, suffix=None):
        archived_filename = os.path.basename(filename)
        if suffix is not None:
            filename_parts = archived_filename.split('.')
            if len(filename_parts) == 1:
                archived_filename = "{}_{}".format(archived_filename, suffix)
            else:
                archived_filename = "{}_{}.{}".format(
                    '.'.join(filename_parts[:-1]), suffix, filename_parts[-1])
        archived_filename = os.path.join(self._run_output_dir, archived_filename)

        if src_dir:
            filename = os.path.join(src_dir, filename)

        if os.path.exists(filename):
            shutil.copy(filename, archived_filename)
