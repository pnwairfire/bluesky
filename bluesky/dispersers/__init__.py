"""bluesky.dispersers

TODO: Move this package into it's own repo. One thing that would need to be
done first is to remove the dependence on bluesky.models.fires.Fire.
This would be fairly easy, since Fire objects are for the most part dicts.
Attr access of top level keys would need to be replaced with direct key
access, and the logic in Fire.latitude and Fire.longitude would need to be
moved into hysplit.py.
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

import abc
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import timedelta

from pyairfire.datetime import parsing as datetime_parsing

from bluesky import datautils
from bluesky.datetimeutils import parse_utc_offset
from bluesky.models.fires import Fire

# TODO: move this to common/reusable module
class create_working_dir(object):
    def __enter__(self):
        self._original_dir = os.getcwd()
        self._working_dir = tempfile.mkdtemp()
        logging.debug('Running hysplit in {}'.format(self._working_dir))
        os.chdir(self._working_dir)
        return self._working_dir

    def __exit__(self, type, value, traceback):
        os.chdir(self._original_dir)
        # TODO: delete self._working_dir or just let os clean it up ?

# Note: HYSPLIT can accept concentrations in any units, but for
# consistency with CALPUFF and other dispersion models, we convert to
# grams in the emissions file.
GRAMS_PER_TON = 907184.74
SECONDS_PER_HR = 60 * 60
TONS_PER_HR_TO_GRAMS_PER_SEC = GRAMS_PER_TON / SECONDS_PER_HR
BTU_TO_MW = 3414425.94972     # Btu to MW

# Conversion factor for fire size
SQUARE_METERS_PER_ACRE = 4046.8726

class DispersionBase(object):

    __metaclass__ = abc.ABCMeta

    # 'BINARIES' dict should be defined by each subclass which depend on
    # external binaries
    BINARIES = {}

    # 'DEFAULTS' object should be defined by each subclass that has default
    # configuration settings (such as in a defaults module)
    DEFAULTS = None

    PHASES = ['flaming', 'smoldering', 'residual']
    TIMEPROFILE_FIELDS = PHASES + ['area_fraction']

    def __init__(self, met_info, **config):
        self._config = config
        # TODO: iterate through self.BINARIES.values() making sure each
        #   exists (though maybe only log warning if doesn't exist, since
        #   they might not all be called for each run
        # TODO: define and call method (which should rely on constant defined
        #   in model-specific classes) which makes sure all required config
        #   options are defined

    def config(self, key):
        # check if key is defined, in order, a) in the config as is, b) in
        # the config as lower case, c) in the hardcoded defaults
        return self._config.get(key,
            self._config.get(key.lower(),
                getattr(self.DEFAULTS, key, None)))

    def run(self, fires, start, num_hours, dest_dir, output_dir_name):
        """Runs hysplit

        args:
         - fires - list of fires to run through hysplit
         - start - model run start hour
         - num_hours - number of hours in model run
         - dest_dir - directory to contain output dir
         - output_dir_name - name of output dir
        """
        logging.info("Running %s", self.__class__.__name__)
        if start.minute or start.second or start.microsecond:
            raise ValueError("Dispersion start time must be on the hour.")
        if type(num_hours) != int:
            raise ValueError("Dispersion num_hours must be an integer.")
        self._model_start = start
        self._num_hours = num_hours

        self._run_output_dir = os.path.join(os.path.abspath(dest_dir),
            output_dir_name)
        os.makedirs(self._run_output_dir)

        self._set_fire_data(fires)

        with create_working_dir() as wdir:
            r = self._run(wdir)

        r.update({
            "directory": self._run_output_dir,
            "start_time": self._model_start.isoformat(),
            "num_hours": self._num_hours
        })
        return r


    @abc.abstractmethod
    def _required_growth_fields(self):
        pass

    @abc.abstractmethod
    def _run(wdir):
        """Underlying run method to be implemented by subclasses
        """
        pass


    # TODO: set these to None, and let _write_emissions using it's logic to
    #  handle missing data?
    # TODO: is this an appropriate fill-in plumerise hour?
    # MISSING_PLUMERISE_HOUR = dict({'percentile_%03d'%(5*e): 0.0 for e in range(21)},
    #     smolder_fraction=0.0)
    # # TODO: is this an appropriate fill-in timeprofile hour?
    # MISSING_TIMEPROFILE_HOUR = {p: 0.0 for p in PHASES }

    def _set_fire_data(self, fires):
        self._fires = []

        # TODO: aggreagating over all fires (if psossible)
        #  use self.model_start and self.model_end
        #  as disperion time window, and then look at
        #  growth window(s) of each fire to fill in emissions for each
        #  fire spanning hysplit time window
        # TODO: determine set of arl fires by aggregating arl files
        #  specified per growth per fire, or expect global arl files
        #  specifications?  (if aggregating over fires, make sure they're
        #  conistent with met domain; if not, raise exception or run them
        #  separately...raising exception would be easier for now)
        # Make sure met files span dispersion time window
        for fire in fires:
            try:
                if 'growth' not in fire:
                    raise ValueError(
                        "Missing timeprofile and plumerise data required for computing dispersion")
                growth_fields = self._required_growth_fields()
                for g in fire.growth:
                    if any([not g.get(f) for f in growth_fields]):
                        raise ValueError("Each growth window must have {} in "
                            "order to compute {} dispersion".format(
                            ','.join(growth_fields), self.__class__.__name__))
                if ('fuelbeds' not in fire or
                        any([not fb.get('emissions') for fb in fire.fuelbeds])):
                    raise ValueError(
                        "Missing emissions data required for computing dispersion")
                # TODO: figure out what to do with heat????  here's the check from
                # BSF's hysplit.py
                # if fire.emissions.sum("heat") < 1.0e-6:
                #     logging.debug("Fire %s has less than 1.0e-6 total heat; skip...", fire.id)
                #     continue

                utc_offset = fire.get('location', {}).get('utc_offset')
                utc_offset = parse_utc_offset(utc_offset) if utc_offset else 0.0

                # TODO: only include plumerise and timeprofile keys within model run
                # time window; and somehow fill in gaps (is this possible?)
                all_plumerise = self._convert_keys_to_datetime(
                    reduce(lambda r, g: r.update(g.get('plumerise', {})) or r, fire.growth, {}))
                all_timeprofile = self._convert_keys_to_datetime(
                    reduce(lambda r, g: r.update(g['timeprofile']) or r, fire.growth, {}))
                plumerise = {}
                timeprofile = {}
                for i in range(self._num_hours):
                    local_dt = self._model_start + timedelta(hours=(i + utc_offset))
                    plumerise[local_dt] = all_plumerise.get(local_dt) # or self.MISSING_PLUMERISE_HOUR
                    timeprofile[local_dt] = all_timeprofile.get(local_dt) #or self.MISSING_TIMEPROFILE_HOUR

                # sum the emissions across all fuelbeds, but keep them separate by phase
                emissions = {p: {} for p in self.PHASES}
                for fb in fire.fuelbeds:
                    for p in self.PHASES:
                        for s in fb['emissions'][p]:
                            emissions[p][s] = (emissions[p].get(s, 0.0)
                                + sum(fb['emissions'][p][s]))

                timeprofiled_emissions = {}
                for dt in timeprofile:
                    timeprofiled_emissions[dt] = {}
                    for e in ('PM25', 'CO'):
                        timeprofiled_emissions[dt][e] = sum([
                            timeprofile[dt][p]*emissions[p].get('PM25', 0.0)
                                for p in self.PHASES
                        ])

                consumption = datautils.sum_nested_data(
                    [fb.get("consumption", {}) for fb in fire['fuelbeds']], 'summary', 'total')

                f = Fire(
                    id=fire.id,
                    meta=fire.get('meta', {}),
                    start=fire.growth[0]['start'],
                    area=fire.location['area'],
                    latitude=fire.latitude,
                    longitude=fire.longitude,
                    utc_offset=utc_offset,
                    plumerise=plumerise,
                    timeprofile=timeprofile,
                    emissions=emissions,
                    timeprofiled_emissions=timeprofiled_emissions,
                    consumption=consumption
                )
                self._fires.append(f)

            except:
                if self.config('skip_invalid_fires'):
                    continue
                else:
                    raise

    def _convert_keys_to_datetime(self, d):
        return { datetime_parsing.parse(k): v for k, v in d.items() }

    def _archive_file(self, filename, src_dir=None, suffix=None):
        if suffix:
            filename_parts = filename.split('.')
            archived_filename = "{}_{}.{}".format(
                '.'.join(filename_parts[:-1]), suffix, filename_parts[-1])
        else:
            archived_filename = filename
        archived_filename = os.path.join(self._run_output_dir, archived_filename)

        if src_dir:
            filename = os.path.join(src_dir, filename)

        shutil.copy(filename, archived_filename)

    def _execute(self, *args, **kwargs):
        # TODO: make sure this is the corrrect way to call
        logging.debug('Executing {}'.format(' '.join(args)))
        # Use check_output so that output isn't sent to stdout
        output = subprocess.check_output(args, cwd=kwargs.get('working_dir'))
        if logging.getLogger().getEffectiveLevel() == logging.DEBUG:
            logging.debug('Captured {} output:'.format(args[0]))
            for line in output.split('\n'):
                logging.debug('{}: {}'.format(args[0], line))
