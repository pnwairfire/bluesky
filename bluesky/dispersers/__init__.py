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
import os
import shutil
import subprocess
from datetime import timedelta

from pyairfire import osutils
from afdatetime import parsing as datetime_parsing

from bluesky import datautils, locationutils
from bluesky.config import Config
from bluesky.datetimeutils import parse_utc_offset
from bluesky.models.fires import Fire
from functools import reduce


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
TIMEPROFILE_FIELDS = PHASES + ['area_fraction']

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
        _c = Config.get('dispersion', self._model)
        for c in sorted(_c.keys()):
            logging.debug('Dispersion config setting - %s = %s', c, _c[c])

    def config(self, *keys, **kwargs):
        return Config.get('dispersion', self._model, *keys, **kwargs)

    def run(self, fires, start, num_hours, output_dir, working_dir=None):
        """Runs hysplit

        args:
         - fires - list of fires to run through hysplit
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

        self._set_fire_data(fires)

        with osutils.create_working_dir(working_dir=self._working_dir) as wdir:
            r = self._run(wdir)

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
        emission_fractions=[0.5] * 20,
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
        for fire in fires:
            try:
                if 'activity' not in fire:
                    raise ValueError(
                        "Missing fire activity data required for computing dispersion")
                activity_fields = self._required_activity_fields() + ('fuelbeds', 'location')
                for a in fire.activity:
                    if any([not a.get(f) for f in activity_fields]):
                        raise ValueError("Each activity window must have {} in "
                            "order to compute {} dispersion".format(
                            ','.join(activity_fields), self.__class__.__name__))
                    if any([not fb.get('emissions') for fb in a['fuelbeds']]):
                        raise ValueError(
                            "Missing emissions data required for computing dispersion")

                    # TDOO: handle case where heat is defined by phase, but not total
                    #   (just make sure each phase is defined, and set total to sum)
                    heat = None
                    heat_values = list(itertools.chain.from_iterable(
                        [fb.get('heat', {}).get('total', [None]) for fb in a['fuelbeds']]))
                    if not any([v is None for v in heat_values]):
                        heat = sum(heat_values)
                        if heat < 1.0e-6:
                            logging.debug("Fire %s activity window %s - %s has "
                                "less than 1.0e-6 total heat; skip...",
                                fire.id, a['start'], a['end'])
                            continue
                    # else, just forget about heat

                    utc_offset = a.get('location', {}).get('utc_offset')
                    utc_offset = parse_utc_offset(utc_offset) if utc_offset else 0.0

                    # TODO: only include plumerise and timeprofile keys within model run
                    # time window; and somehow fill in gaps (is this possible?)
                    all_plumerise = a.get('plumerise', {})
                    all_timeprofile = a.get('timeprofile', {})
                    plumerise = {}
                    timeprofile = {}
                    for i in range(self._num_hours):
                        local_dt = self._model_start + timedelta(hours=(i + utc_offset))
                        # TODO: will all_plumerise and all_timeprofile always
                        #    have string value keys
                        local_dt = local_dt.strftime('%Y-%m-%dT%H:%M:%S')
                        plumerise[local_dt] = all_plumerise.get(local_dt) or self.MISSING_PLUMERISE_HOUR
                        timeprofile[local_dt] = all_timeprofile.get(local_dt) or self.MISSING_TIMEPROFILE_HOUR

                    # sum the emissions across all fuelbeds, but keep them separate by phase
                    emissions = {p: {} for p in PHASES}
                    for fb in a['fuelbeds']:
                        for p in PHASES:
                            for s in fb['emissions'][p]:
                                emissions[p][s] = (emissions[p].get(s, 0.0)
                                    + sum(fb['emissions'][p][s]))

                    timeprofiled_emissions = {}
                    for dt in timeprofile:
                        timeprofiled_emissions[dt] = {}
                        for e in self.SPECIES:
                            timeprofiled_emissions[dt][e] = sum([
                                timeprofile[dt][p]*emissions[p].get('PM2.5', 0.0)
                                    for p in PHASES
                            ])

                    # consumption = datautils.sum_nested_data(
                    #     [fb.get("consumption", {}) for fb in a['fuelbeds']], 'summary', 'total')
                    consumption = a['consumption']['summary']

                    latlng = locationutils.LatLng(a['location'])

                    f = Fire(
                        id=fire.id,
                        meta=fire.get('meta', {}),
                        start=a['start'],
                        area=a['location']['area'],
                        latitude=latlng.latitude,
                        longitude=latlng.longitude,
                        utc_offset=utc_offset,
                        plumerise=plumerise,
                        timeprofile=timeprofile,
                        emissions=emissions,
                        timeprofiled_emissions=timeprofiled_emissions,
                        consumption=consumption
                    )
                    if heat:
                        f['heat'] = heat
                    self._fires.append(f)

            except:
                if self.config('skip_invalid_fires'):
                    continue
                else:
                    raise

    def _convert_keys_to_datetime(self, d):
        return { datetime_parsing.parse(k): v for k, v in d.items() }

    def _archive_file(self, filename, src_dir=None, suffix=None):
        archived_filename = os.path.basename(filename)
        if suffix:
            filename_parts = archived_filename.split('.')
            archived_filename = "{}_{}.{}".format(
                '.'.join(filename_parts[:-1]), suffix, filename_parts[-1])
        archived_filename = os.path.join(self._run_output_dir, archived_filename)

        if src_dir:
            filename = os.path.join(src_dir, filename)

        if os.path.exists(filename):
            shutil.copy(filename, archived_filename)

    def _execute(self, *args, **kwargs):
        # TODO: make sure this is the corrrect way to call
        logging.debug('Executing {}'.format(' '.join(args)))
        # Use check_output so that output isn't sent to stdout
        output = subprocess.check_output(args, cwd=kwargs.get('working_dir'))
        output = output.decode('ascii')
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            logging.debug('Captured {} output:'.format(args[0]))
            for line in output.split('\n'):
                logging.debug('{}: {}'.format(args[0], line))
