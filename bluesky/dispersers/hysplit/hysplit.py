"""bluesky.dispersers.hysplit.hysplit

The code in this module was copied from BlueSky Framework, and modified
significantly.  It was originally written by Sonoma Technology, Inc.

v0.2.0 introduced a number of chnanges migrated from BSF's hysplit v8.
Heres are the notes coped from BSF:

    '''
        Version 8 - modifications Dec 2015, rcs

         1) greatly expanded user access to variables in the hysplit
            CONTROL and SETUP.CFG files
         2) heavily modified the way particle initialization files are
            created/read, including support for MPI (read and write)
            runs but not for TODO tranched runs

            READ_INIT_FILE is not longer supported, instead use NINIT
                to control if and how to read in PARINIT file

            HYSPLIT_SETUP_CFG is no longer supported. instead include
                the SETUP.CFG variable one wishes to set in the .ini
                list of supported vars:
                NCYCL, NDUMP, KHMAX, NINIT, INITD, PARINIT, PARDUMP,
                QCYCLE, TRATIO, DELT, NUMPAR, MAXPAR, MGMIN and
                ICHEM

                PARINIT & PARDUMP can both handle strftime strings in
                      their names.
                      NOTE: full path name length must be <= 80 chars.

            new variables now accessible in the CONTROL file are
                three sampling interv opts (type, hour and minutes),
                three particle opts (diameter, density, shape),
                five dry dep opts (vel, mol weight, reactivity,
                                   diffusivity, henry const),
                three wet dep opts (henry, in-cloud scavenging ratio,
                                    below-cloud scav coef),
                radioactive half-life and
                resusspension constant
    '''
"""

__author__ = "Joel Dubowy and Sonoma Technology, Inc."

__version__ = "0.2.0"

import copy
import logging
import math
import os
import shutil
# import tarfile
import threading
import datetime

from afdatetime.parsing import parse_datetime

from bluesky import io
from bluesky.config import Config
from bluesky.models.fires import Fire
from .. import (
    DispersionBase, GRAMS_PER_TON, SQUARE_METERS_PER_ACRE, PHASES
)

from . import hysplit_utils

__all__ = [
    'HYSPLITDispersion'
]

DEFAULT_BINARIES = {
    'HYSPLIT': {
        "old_config_key": "HYSPLIT_BINARY",
        "default":"hycs_std"
    },
    'HYSPLIT_MPI': {
        "old_config_key": "HYSPLIT_MPI_BINARY",
        "default":"hycm_std"
    },
    'NCEA': {
        "old_config_key": "NCEA_EXECUTABLE",
        "default":"ncea"
    },
    'NCKS': {
        "old_config_key": "NCKS_EXECUTABLE",
        "default":"ncks"
    },
    'MPI': {
        "old_config_key": "MPIEXEC",
        "default":"mpiexec"
    },
    'HYSPLIT2NETCDF': {
        "old_config_key": "HYSPLIT2NETCDF_BINARY",
        "default":"hysplit2netcdf"
    }
}

def _get_binaries(config_getter):
    """The various executables can be specified either
    using the old BSF config keys or the new keys nested
    under 'binaries'. e.g.

    Old:
        {
            ...,
            "config": {
                "hysplit": {
                    "HYSPLIT_BINARY": "hycs_std",
                    "HYSPLIT_MPI_BINARY": "hycm_std",
                    "NCEA_EXECUTABLE": "ncea",
                    "NCKS_EXECUTABLE": "ncks",
                    "MPIEXEC": "mpiexec",
                    "HYSPLIT2NETCDF_BINARY": "hysplit2netcdf"
                }
            }
            ...
        }

    New:
        {
            ...,
            "config": {
                "hysplit": {
                    "binaries" : {
                        'hysplit': "hycs_std",
                        'hysplit_mpi': "hycm_std",
                        'ncea': "ncea",
                        'ncks': "ncks",
                        'mpi': "mpiexec",
                        'hysplit2netcdf': "hysplit2netcdf"
                    }
                }
            }
            ...
        }

    The new way takes precedence over the old.
    """

    binaries = {}
    for k, d in DEFAULT_BINARIES.items():
        # config_getter will try upper and lower case
        # versions of k and d['old_config_key']
        binaries[k] = (config_getter('binaries', k, allow_missing=True)
            or config_getter(d['old_config_key'], allow_missing=True)
            or d['default'])
    return binaries

class HYSPLITDispersion(DispersionBase):
    """ HYSPLIT Dispersion model

    HYSPLIT Concentration model version 4.9

    TODO: determine which config options we'll support
    """

    def __init__(self, met_info, **config):
        super(HYSPLITDispersion, self).__init__(met_info, **config)

        self.BINARIES = _get_binaries(self.config)

        self._set_met_info(copy.deepcopy(met_info))
        self._output_file_name = self.config('output_file_name')
        self._has_parinit = []

    def _required_activity_fields(self):
        return ('timeprofile', 'plumerise', 'emissions')

    def _run(self, wdir):
        """Runs hysplit

        args:
         - wdir -- working directory
        """
        dispersion_offset = int(self.config("DISPERSION_OFFSET") or 0)
        self._model_start += datetime.timedelta(hours=dispersion_offset)
        self._num_hours -= dispersion_offset
        self._adjust_dispersion_window_for_available_met()

        self._set_grid_params()
        self._set_reduction_factor()
        self._compute_tranches()
        hysplit_utils.fill_in_dummy_fires(self._fire_sets, self._fires,
            self._num_processes, self._model_start, self._num_hours,
            self._grid_params)

        if 1 < self._num_processes:
                # hysplit_utils.create_fire_tranches will log number of processes
                # and number of fires each
                self._run_parallel(wdir)
        else:
            self._run_process(self._fires, wdir)

        # Note: DispersionBase.run will add directory, start_time,
        #  and num_hours to the response dict
        self._met_info.pop('hours')
        self._met_info['files'] = list(self._met_info['files'])
        return {
            "output": {
                "grid_filetype": "NETCDF",
                "grid_filename": self._output_file_name,
                "parameters": {"pm25": "PM25"},
                "grid_parameters": self._grid_params
            },
            "num_processes": self._num_processes,
            "met_info": self._met_info,
            "carryover": {
                "any": bool(self._has_parinit) and any(self._has_parinit),
                "all": bool(self._has_parinit) and all(self._has_parinit)
            }
        }

    ##
    ## Seting met info
    ##

    def _get_met_file(self, met_file_info):
        if not met_file_info.get('file'):
            raise ValueError("ARL file not defined for specified date range")
        if not os.path.exists(met_file_info['file']):
            raise ValueError("ARL file does not exist: {}".format(
                met_file_info['file']))
        return met_file_info['file']

    def _get_met_hours(self, met_file_info):
        first_hour = parse_datetime(met_file_info['first_hour'], 'first_hour')
        last_hour = parse_datetime(met_file_info['last_hour'], 'last_hour')
        hours = [first_hour + datetime.timedelta(hours=n)
            for n in range(int((last_hour-first_hour).total_seconds() / 3600) + 1)]
        return hours

    def _set_met_info(self, met_info):
        # TODO: move validation code into common module met.arl.validation ?
        self._met_info = {}

        if met_info.get('grid'):
            self._met_info['grid'] = met_info['grid']
        # The grid fields, 'domain', 'boundary', and 'grid_spacing_km' can be
        # defined either in the met object or in the hsyplit config. Expections
        # will be raised downstream if not defined in either place

        # hysplit just needs the name, but we need to know the hours with
        # met data for adjusting dispersion time dinwow
        self._met_info['files'] = set()
        self._met_info['hours'] = set()

        if not met_info.get('files'):
            raise ValueError("Met info lacking arl file information")
        for met_file_info in met_info.pop('files'):
            self._met_info['files'].add(self._get_met_file(met_file_info))
            self._met_info['hours'].update(self._get_met_hours(met_file_info))

    def _adjust_dispersion_window_for_available_met(self):
        n = 0
        while n < self._num_hours:
            hr = self._model_start + datetime.timedelta(hours=n)
            if hr not in self._met_info['hours']:
                break
            n += 1
        if n == 0:
            raise ValueError(
                "No ARL met data for first hour of dispersion window")
        elif n < self._num_hours:
            self._record_warning("Incomplete met. Running dispersion for"
                " {} hours instead of {}".format(n, self._num_hours))
            self._num_hours = n


    # Number of quantiles in vertical emissions allocation scheme
    NQUANTILES = 20

    def _set_reduction_factor(self):
        """Retrieve factor for reducing the number of vertical emission levels"""

        #    Ensure the factor divides evenly into the number of quantiles.
        #    For the 20 quantile vertical accounting scheme, the following values are appropriate:
        #       reductionFactor = 1 .... 20 emission levels (no change from the original scheme)
        #       reductionFactor = 2......10 emission levels
        #       reductionFactor = 4......5 emission levels
        #       reductionFactor = 5......4 emission levels
        #       reductionFactor = 10.....2 emission levels
        #       reductionFactor = 20.....1 emission level

        # Pull reduction factor from user input
        self._reduction_factor = self.config("VERTICAL_EMISLEVELS_REDUCTION_FACTOR")
        self._reduction_factor = int(self._reduction_factor)

        # Ensure a valid reduction factor
        if self._reduction_factor > self.NQUANTILES:
            self._reduction_factor = self.NQUANTILES
            logging.debug("VERTICAL_EMISLEVELS_REDUCTION_FACTOR reset to %s" % str(self.NQUANTILES))
        elif self._reduction_factor <= 0:
            self._reduction_factor = 1
            logging.debug("VERTICAL_EMISLEVELS_REDUCTION_FACTOR reset to 1")
        while (self.NQUANTILES % self._reduction_factor) != 0:  # make sure factor evenly divides into the number of quantiles
            self._reduction_factor -= 1
            logging.debug("VERTICAL_EMISLEVELS_REDUCTION_FACTOR reset to %s" % str(self._reduction_factor))

        self.num_output_quantiles = self.NQUANTILES // self._reduction_factor

        if self._reduction_factor != 1:
            logging.info("Number of vertical emission levels reduced by factor of %s" % str(self._reduction_factor))
            logging.info("Number of vertical emission quantiles will be %s" % str(self.num_output_quantiles))

    def _compute_tranches(self):
        tranching_config = {
            'num_processes': self.config("NPROCESSES"),
            'num_fires_per_process': self.config("NFIRES_PER_PROCESS"),
            'num_processes_max': self.config("NPROCESSES_MAX"),
            # The 'or 0' handles None value
            'parinit_or_pardump': int(self.config("NINIT") or 0) > 0
                or self.config("MAKE_INIT_FILE")
        }

        # Note: organizing the fire sets is wasted computation if we end up
        # running only one process, but doing so before looking at the
        # NPROCESSES, NFIRES_PER_PROCESS, NPROCESSES_MAX config values allows
        # for more code to be encapsulated in hysplit_utils, which then allows
        # for greater testability.  (hysplit_utils.create_fire_sets could be
        # skipped if either NPROCESSES > 1 or NFIRES_PER_PROCESS > 1)
        self._fire_sets = hysplit_utils.create_fire_sets(self._fires)
        self._num_processes = hysplit_utils.compute_num_processes(
            len(self._fire_sets), **tranching_config)

    def _run_parallel(self, working_dir):
        runner = self
        class T(threading.Thread):
            def  __init__(self, fires, config, working_dir, tranche_num):
                super(T, self).__init__()
                self.fires = fires
                self.config = config
                self.working_dir = working_dir
                if not os.path.exists(working_dir):
                    os.makedirs(working_dir)
                self.tranche_num = tranche_num
                self.exc = None

            def run(self):
                # We need to set config to what was loaded in the main thread.
                # Otherwise, we'll just be using defaults
                Config().set(self.config)
                try:
                    runner._run_process(self.fires, self.working_dir,
                        self.tranche_num)
                except Exception as e:
                    self.exc = e

        fire_tranches = hysplit_utils.create_fire_tranches(
            self._fire_sets, self._num_processes)
        threads = []
        main_thread_config = Config().get()
        for nproc in range(len(fire_tranches)):
            fires = fire_tranches[nproc]
            # Note: no need to set _context.basedir; it will be set to workdir
            logging.info("Starting thread to run HYSPLIT on %d fires." % (len(fires)))
            t = T(fires, main_thread_config,
                os.path.join(working_dir, str(nproc)), nproc)
            t.start()
            threads.append(t)

        # If there were any exceptions, raise one of them after joining all threads
        exc = None
        for t in threads:
            t.join()
            if t.exc:
                exc = t.exc # TODO: just raise exception here, possibly before all threads have been joined?
        if exc:
            raise exc

        #  'ttl' is sum of values; see http://nco.sourceforge.net/nco.html#Operation-Types
        # sum together all the PM2.5 fields then append the TFLAG field from
        # one of the individual runs (they're all the same)
        # using run 0 as it should always be present regardless of how many
        # processes were used....
        # prevents ncea from adding all the TFLAGs together and mucking up the
        # date

        output_file = os.path.join(working_dir, self._output_file_name)

        #ncea_args = ["-y", "ttl", "-O"]
        ncea_args = ["-O","-v","PM25","-y","ttl"]
        ncea_args.extend(["%d/%s" % (i, self._output_file_name) for i in  range(self._num_processes)])
        ncea_args.append(output_file)
        io.SubprocessExecutor().execute(self.BINARIES['NCEA'], *ncea_args, cwd=working_dir)

        ncks_args = ["-A","-v","TFLAG"]
        ncks_args.append("0/%s" % (self._output_file_name))
        ncks_args.append(output_file)
        io.SubprocessExecutor().execute(self.BINARIES['NCKS'], *ncks_args, cwd=working_dir)
        self._archive_file(output_file)

    def _create_sym_link(self, dest, link):
        try:
            os.symlink(dest, link)
        except FileExistsError as e:
            # ignore existing sym link error
            pass

    def _run_process(self, fires, working_dir, tranche_num=None):
        logging.info("Running one HYSPLIT49 Dispersion model process")
        # TODO: set all but fires, working_dir, and tranche_num as instance
        # properties in self.run so that they don't have to be passed into
        # each call to _run_process.
        # The only things that change from call to call are working_dir,
        # fires, and tranche_num
        self._create_sym_links_for_process(working_dir)

        emissions_file = os.path.join(working_dir, "EMISS.CFG")
        control_file = os.path.join(working_dir, "CONTROL")
        setup_file = os.path.join(working_dir, "SETUP.CFG")
        message_files = [os.path.join(working_dir, "MESSAGE")]
        output_conc_file = os.path.join(working_dir, "hysplit.con")
        output_file = os.path.join(working_dir, self._output_file_name)

        # NINIT: sets how particle init file is to be used
        #  0 = no particle initialization file read (default)
        #  1 = read parinit file only once at initialization time
        #  2 = check each hour, if there is a match then read those values in
        #  3 = like '2' but replace emissions instead of adding to existing
        #      particles
        ninit_val = int(self.config("NINIT") or 0)

        # need an input file if ninit_val > 0
        if ninit_val > 0:
            # name of pardump input file, parinit (check for strftime strings)
            parinit = self.config("PARINIT")
            if "%" in parinit:
                parinit = self._model_start.strftime(parinit)
            if tranche_num is not None:
                parinit = parinit + "-" + str(tranche_num).zfill(2)
            parinitFiles = [ parinit ]

            # if an MPI run need to create the full list of expected files
            # based on the number of CPUs
            if self.config("MPI"):
                NCPUS = self.config("NCPUS")
                parinitFiles = ["%s.%3.3i" % ( parinit, (i+1)) for i in range(NCPUS)]

            # loop over parinitFiles check if exists.
            # for MPI runs check that all files exist...if any in the list
            # don't exist raise exception if STOP_IF_NO_PARINIT is True
            # if STOP_IF_NO_PARINIT is False and all/some files don't exist,
            # set ninit_val to 0 and issue warning.
            for f in parinitFiles:
                if not os.path.exists(f):
                    if self.config("STOP_IF_NO_PARINIT"):
                        msg = "Matching particle init file, %s, not found. Stop." % f
                        raise Exception(msg)

                    msg = "No matching particle initialization file, %s, found; Using no particle initialization" % f
                    logging.warning(msg)
                    logging.debug(msg)
                    ninit_val = 0
                    self._has_parinit.append(False)

                else:
                    logging.info("Using particle initialization file %s" % f)
                    self._has_parinit.append(True)

        # Prepare for run ... get pardump name just in case needed
        pardump = self.config("PARDUMP")
        if "%" in pardump:
            pardump = self._model_start.strftime(pardump)
        if tranche_num is not None:
            pardump = pardump + '-' + str(tranche_num).zfill(2)
        pardumpFiles = [ pardump ]

        # If MPI run
        if self.config("MPI"):
            NCPUS = self.config("NCPUS")
            logging.info("Running MPI HYSPLIT with %s processors." % NCPUS)
            if NCPUS < 1:
                logging.warning("Invalid NCPUS specified...resetting NCPUS to 1 for this run.")
                NCPUS = 1

            message_files = ["MESSAGE.%3.3i" % (i+1) for i in range(NCPUS)]

            # name of the pardump files (one for each CPU)
            if self.config("MAKE_INIT_FILE"):
                pardumpFiles = ["%s.%3.3i" % ( pardump, (i+1)) for i in range(NCPUS)]

            # what command do we use to issue an mpi version of hysplit

            # TODO: either update the following checks for self.BINARIES['MPI'] and
            # self.BINARIES['HYSPLIT_MPI'] to try running with -v or -h option or
            # something similar,  or remove them
            # if not os.path.isfile(self.BINARIES['MPI']):
            #     msg = "Failed to find %s. Check self.BINARIES['MPI'] setting and/or your MPICH2 installation." % mpiexec
            #     raise AssertionError(msg)
            # if not os.path.isfile(self.BINARIES['HYSPLIT_MPI']):
            #     msg = "HYSPLIT MPI executable %s not found." % self.BINARIES['HYSPLIT_MPI']
            #     raise AssertionError(msg)

        # Else single cpu run
        else:
            NCPUS = 1

        self._write_emissions(fires, emissions_file)
        self._write_control_file(fires, control_file, output_conc_file)
        self._write_setup_file(fires, emissions_file, setup_file, ninit_val, NCPUS, tranche_num)

        try:
            # Run HYSPLIT
            if self.config("MPI"):
                args = [self.BINARIES['MPI']]
                if self.BINARIES['MPI'] == 'mpiexec':
                    # In case docker is being used, use '--allow-run-as-root'
                    # with `mpiexec` binary.  (mpiexec.hydra doesn't need
                    # or even support it.)
                    args.append("--allow-run-as-root")
                args.extend(["-n", str(NCPUS), self.BINARIES['HYSPLIT_MPI']])
                io.SubprocessExecutor().execute(*args, cwd=working_dir)
            else:  # standard serial run
                io.SubprocessExecutor().execute(self.BINARIES['HYSPLIT'], cwd=working_dir)

            if not os.path.exists(output_conc_file):
                msg = "HYSPLIT failed, check MESSAGE file for details"
                raise AssertionError(msg)
            self._archive_file(output_conc_file, tranche_num=tranche_num)

            if self.config('CONVERT_HYSPLIT2NETCDF'):
                logging.info("Converting HYSPLIT output to NetCDF format: %s -> %s" % (output_conc_file, output_file))
                io.SubprocessExecutor().execute(self.BINARIES['HYSPLIT2NETCDF'],
                    "-I" + output_conc_file,
                    "-O" + os.path.basename(output_file),
                    "-X1000000.0",  # Scale factor to convert from grams to micrograms
                    "-D1",  # Debug flag
                    "-L-1",  # Lx is x layers. x=-1 for all layers...breaks KML output for multiple layers
                    cwd=working_dir
                )

                if not os.path.exists(output_file):
                    msg = "Unable to convert HYSPLIT concentration file to NetCDF format"
                    raise AssertionError(msg)
            self._archive_file(output_file, tranche_num=tranche_num)

        finally:
            # Archive input files
            self._archive_file(emissions_file, tranche_num=tranche_num)
            self._archive_file(control_file, tranche_num=tranche_num)
            self._archive_file(setup_file, tranche_num=tranche_num)

            # Archive data files
            for f in message_files:
                self._archive_file(f, tranche_num=tranche_num)
            if self.config("MAKE_INIT_FILE") and self.config('archive_pardump_files'):
                for f in pardumpFiles:
                    self._archive_file(f, tranche_num=tranche_num)
                    #shutil.copy2(os.path.join(working_dir, f), self._run_output_dir)

    def _archive_file(self, filename, tranche_num=None):
        if tranche_num is None:
            super()._archive_file(filename)
        # Only archive tranched files if configured to do so
        elif self.config('archive_tranche_files'):
            super()._archive_file(filename, suffix=tranche_num)

    def _create_sym_links_for_process(self, working_dir):
        for f in self._met_info['files']:
            # bluesky.modules.dispersion.run will have weeded out met
            # files that aren't relevant to this dispersion run
            self._create_sym_link(f,
                os.path.join(working_dir, os.path.basename(f)))

        # Create sym links to ancillary data files (note: HYSPLIT49 balks
        # if it can't find ASCDATA.CFG).
        self._create_sym_link(self.config("ASCDATA_FILE"),
            os.path.join(working_dir, 'ASCDATA.CFG'))
        self._create_sym_link(self.config("LANDUSE_FILE"),
            os.path.join(working_dir, 'LANDUSE.ASC'))
        self._create_sym_link(self.config("ROUGLEN_FILE"),
            os.path.join(working_dir, 'ROUGLEN.ASC'))

    def _get_hour_data(self, dt, fire):
        if fire.plumerise and fire.timeprofiled_emissions and fire.timeprofiled_area:
            local_dt = dt + datetime.timedelta(hours=fire.utc_offset)
            # TODO: will fire.plumerise and fire.timeprofile always
            #    have string value keys
            local_dt = local_dt.strftime('%Y-%m-%dT%H:%M:%S')
            plumerise_hour = fire.plumerise.get(local_dt)
            timeprofiled_emissions_hour = fire.timeprofiled_emissions.get(local_dt)
            hourly_area = fire.timeprofiled_area.get(local_dt)
            if plumerise_hour and timeprofiled_emissions_hour and hourly_area:
                return False, plumerise_hour, timeprofiled_emissions_hour, hourly_area

        return (True, hysplit_utils.DUMMY_PLUMERISE_HOUR, dict(), 0.0)

    def _write_emissions(self, fires, emissions_file):
        # A value slightly above ground level at which to inject smoldering
        # emissions into the model.
        smolder_height = self.config("SMOLDER_HEIGHT")

        with open(emissions_file, "w") as emis:
            # HYSPLIT skips past the first two records, so these are for comment purposes only
            emis.write("emissions group header: YYYY MM DD HH QINC NUMBER\n")
            emis.write("each emission's source: YYYY MM DD HH MM DUR_HHMM LAT LON HT RATE AREA HEAT\n")

            # Loop through the timesteps
            for hour in range(self._num_hours):
                dt = self._model_start + datetime.timedelta(hours=hour)
                dt_str = dt.strftime("%y %m %d %H")

                num_fires = len(fires)
                #num_heights = 21 # 20 quantile gaps, plus ground level
                num_heights = self.num_output_quantiles + 1
                num_sources = num_fires * num_heights

                # TODO: What is this and what does it do?
                # A reasonable guess would be that it means a time increment of 1 hour
                qinc = 1

                # Write the header line for this timestep
                emis.write("%s %02d %04d\n" % (dt_str, qinc, num_sources))

                fires_wo_emissions = 0

                # Loop through the fire locations
                for fire in fires:
                    # Get some properties from the fire location
                    lat = fire.latitude
                    lon = fire.longitude

                    # If we don't have real data for the given timestep, we apparently need
                    # to stick in dummy records anyway (so we have the correct number of sources).
                    (dummy, plumerise_hour, timeprofiled_emissions_hour,
                        hourly_area) = self._get_hour_data(dt, fire)
                    if dummy:
                        logging.debug("Fire %s has no emissions for hour %s", fire.id, hour)
                        fires_wo_emissions += 1

                    area_meters = 0.0
                    smoldering_fraction = 0.0
                    pm25_injected = 0.0
                    if not dummy:
                        # Extract the fraction of area burned in this timestep, and
                        # convert it from acres to square meters.
                        area_meters = hourly_area * SQUARE_METERS_PER_ACRE

                        smoldering_fraction = plumerise_hour['smolder_fraction']

                        # Compute the total PM2.5 emitted at this timestep (grams) by
                        # multiplying the phase-specific total emissions by the
                        # phase-specific hourly fractions for this hour to get the
                        # hourly emissions by phase for this hour, and then summing
                        # the three values to get the total emissions for this hour
                        # TODO: use fire.timeprofiled_emissions[local_dt]['PM2.5']
                        pm25_emitted = timeprofiled_emissions_hour.get('PM2.5', 0.0)
                        pm25_emitted *= GRAMS_PER_TON
                        # Total PM2.5 smoldering (not lofted in the plume)
                        pm25_injected = pm25_emitted * smoldering_fraction

                    entrainment_fraction = 1.0 - smoldering_fraction

                    # We don't assign any heat, so the PM2.5 mass isn't lofted
                    # any higher.  This is because we are assigning explicit
                    # heights from the plume rise.
                    heat = 0.0

                    # Inject the smoldering fraction of the emissions at ground level
                    # (SMOLDER_HEIGHT represents a value slightly above ground level)
                    height_meters = smolder_height

                    # Write the smoldering record to the file
                    record_fmt = "%s 00 0100 %8.4f %9.4f %6.0f %7.2f %7.2f %15.2f\n"
                    emis.write(record_fmt % (dt_str, lat, lon, height_meters, pm25_injected, area_meters, heat))

                    for level in range(0, len(plumerise_hour['heights']) - 1, self._reduction_factor):
                        height_meters = 0.0
                        pm25_injected = 0.0
                        if not dummy:
                            # Loop through the heights (20 quantiles of smoke density)
                            # For the unreduced case, we loop through 20 quantiles, but we have
                            # 21 quantile-edge measurements.  So for each
                            # quantile gap, we need to find a point halfway
                            # between the two edges and inject that quantile's fraction of total emissions

                            # KJC optimization...
                            # Reduce the number of vertical emission levels by a reduction factor
                            # and place the appropriate fraction of emissions at each level.
                            # ReductionFactor MUST evenly divide into the number of quantiles

                            lower_height = plumerise_hour['heights'][level]
                            upper_height_index = min(level + self._reduction_factor, len(plumerise_hour['heights']) - 1)
                            upper_height = plumerise_hour['heights'][upper_height_index]
                            if self._reduction_factor == 1:
                                height_meters = (lower_height + upper_height) / 2.0  # original approach
                            else:
                                height_meters = upper_height # top-edge approach
                            # Total PM2.5 entrained (lofted in the plume)
                            pm25_entrained = pm25_emitted * entrainment_fraction
                            # Inject the proper fraction of the entrained PM2.5 in each quantile gap.
                            fraction = sum(plumerise_hour['emission_fractions'][level:level+self._reduction_factor])
                            pm25_injected = pm25_entrained * fraction

                        # Write the record to the file
                        emis.write(record_fmt % (dt_str, lat, lon, height_meters, pm25_injected, area_meters, heat))

                if fires_wo_emissions > 0:
                    logging.debug("%d of %d fires had no emissions for hour %d", fires_wo_emissions, num_fires, hour)


    VERTICAL_CHOICES = {
        "DATA": 0,
        "ISOB": 1,
        "ISEN": 2,
        "DENS": 3,
        "SIGMA": 4,
        "DIVERG": 5,
        "ETA": 6
    }
    def _get_vertical_method(self):
        # Vertical motion choices:

        VERTICAL_METHOD = self.config("VERTICAL_METHOD")
        try:
            verticalMethod = self.VERTICAL_CHOICES[VERTICAL_METHOD]
        except KeyError:
            verticalMethod = self.VERTICAL_CHOICES["DATA"]

        return verticalMethod

    def _set_grid_params(self):
        self._grid_params = hysplit_utils.get_grid_params(
            met_info=self._met_info, fires=self._fires)

    def _write_control_file(self, fires, control_file, concFile):
        num_fires = len(fires)
        num_heights = self.num_output_quantiles + 1  # number of quantiles used, plus ground level
        num_sources = num_fires * num_heights

        # An arbitrary height value.  Used for the default source height
        # in the CONTROL file.  This can be anything we want, because
        # the actual source heights are overridden in the EMISS.CFG file.
        sourceHeight = 15.0

        verticalMethod = self._get_vertical_method()

        # Height of the top of the model domain
        modelTop = self.config("TOP_OF_MODEL_DOMAIN")

        #modelEnd = self._model_start + datetime.timedelta(hours=self._num_hours)

        # Build the vertical Levels string
        levels = self.config("VERTICAL_LEVELS")
        numLevels = len(levels)
        verticalLevels = " ".join(str(x) for x in levels)

        # Warn about multiple sampling grid levels and KML/PNG image generation
        if numLevels > 1:
            logging.warning("KML and PNG images will be empty since more than 1 vertical level is selected")

        # To minimize change in the following code, set aliases
        centerLat =  self._grid_params["center_latitude"]
        centerLon = self._grid_params["center_longitude"]
        widthLon = self._grid_params["width_longitude"]
        heightLat = self._grid_params["height_latitude"]
        spacingLon = self._grid_params["spacing_longitude"]
        spacingLat = self._grid_params["spacing_latitude"]

        # Decrease the grid resolution based on number of fires
        if self.config("OPTIMIZE_GRID_RESOLUTION"):
            logging.info("Grid resolution adjustment option invoked")
            minSpacingLon = spacingLon
            minSpacingLat = spacingLat
            maxSpacingLon = self.config("MAX_SPACING_LONGITUDE")
            maxSpacingLat = self.config("MAX_SPACING_LATITUDE")
            intervals = sorted([int(x) for x in self.config("FIRE_INTERVALS")])

            # Maximum grid spacing cannot be smaller than the minimum grid spacing
            if maxSpacingLon < minSpacingLon:
                maxSpacingLon = minSpacingLon
                logging.debug("maxSpacingLon > minSpacingLon...longitude grid spacing will not be adjusted")
            if maxSpacingLat < minSpacingLat:
                maxSpacingLat = minSpacingLat
                logging.debug("maxSpacingLat > minSpacingLat...latitude grid spacing will not be adjusted")

            # Throw out negative intervals
            intervals = [x for x in intervals if x >= 0]

            if len(intervals) == 0:
                intervals = [0,num_fires]
                logging.debug("FIRE_INTERVALS had no values >= 0...grid spacing will not be adjusted")

            # First bin should always start with zero
            if intervals[0] != 0:
                intervals.insert(0,0)
                logging.debug("Zero added to the beginning of FIRE_INTERVALS list")

            # must always have at least 2 intervals
            if len(intervals) < 2:
                intervals = [0,num_fires]
                logging.debug("Need at least two FIRE_INTERVALS...grid spacing will not be adjusted")

            # Increase the grid spacing depending on number of fires
            i = 0
            numBins = len(intervals)
            rangeSpacingLat = (maxSpacingLat - minSpacingLat)/(numBins - 1)
            rangeSpacingLon = (maxSpacingLon - minSpacingLon)/(numBins - 1)
            for interval in intervals:
                if num_fires > interval:
                    spacingLat = minSpacingLat + (i * rangeSpacingLat)
                    spacingLon = minSpacingLon + (i * rangeSpacingLon)
                    i += 1
                logging.debug("Lon,Lat grid spacing for interval %d adjusted to %f,%f" % (interval,spacingLon,spacingLat))
            logging.info("Lon/Lat grid spacing for %d fires will be %f,%f" % (num_fires,spacingLon,spacingLat))

        # Note: Due to differences in projections, the dimensions of this
        #       output grid are conservatively large.
        logging.info("HYSPLIT grid CENTER_LATITUDE = %s" % centerLat)
        logging.info("HYSPLIT grid CENTER_LONGITUDE = %s" % centerLon)
        logging.info("HYSPLIT grid HEIGHT_LATITUDE = %s" % heightLat)
        logging.info("HYSPLIT grid WIDTH_LONGITUDE = %s" % widthLon)
        logging.info("HYSPLIT grid SPACING_LATITUDE = %s" % spacingLat)
        logging.info("HYSPLIT grid SPACING_LONGITUDE = %s" % spacingLon)

        with open(control_file, "w") as f:
            # Starting time (year, month, day hour)
            f.write(self._model_start.strftime("%y %m %d %H") + "\n")

            # Number of sources
            f.write("%d\n" % num_sources)

            # Source locations
            for fire in fires:
                for height in range(num_heights):
                    f.write("%9.3f %9.3f %9.3f\n" % (fire.latitude, fire.longitude, sourceHeight))

            # Total run time (hours)
            f.write("%04d\n" % self._num_hours)

            # Method to calculate vertical motion
            f.write("%d\n" % verticalMethod)

            # Top of model domain
            f.write("%9.1f\n" % modelTop)

            # Number of input data grids (met files)
            f.write("%d\n" % len(self._met_info['files']))
            # Directory for input data grid and met file name
            for filename in sorted(self._met_info['files']):
                f.write("./\n")
                f.write("%s\n" % os.path.basename(filename))

            # Number of pollutants = 1 (only modeling PM2.5 for now)
            f.write("1\n")
            # Pollutant ID (4 characters)
            f.write("PM25\n")
            # Emissions rate (per hour) (Ken's code says "Emissions source strength (mass per second)" -- which is right?)
            f.write("0.001\n")
            # Duration of emissions (hours)
            f.write(" %9.3f\n" % self._num_hours)
            # Source release start time (year, month, day, hour, minute)
            f.write("%s\n" % self._model_start.strftime("%y %m %d %H %M"))

            # Number of simultaneous concentration grids
            f.write("1\n")

            # Sampling grid center location (latitude, longitude)
            f.write("%9.3f %9.3f\n" % (centerLat, centerLon))
            # Sampling grid spacing (degrees latitude and longitude)
            f.write("%9.3f %9.3f\n" % (spacingLat, spacingLon))
            # Sampling grid span (degrees latitude and longitude)
            f.write("%9.3f %9.3f\n" % (heightLat, widthLon))

            # Directory of concentration output file
            f.write("./\n")
            # Filename of concentration output file
            f.write("%s\n" % os.path.basename(concFile))

            # Number of vertical concentration levels in output sampling grid
            f.write("%d\n" % numLevels)
            # Height of each sampling level in meters AGL
            f.write("%s\n" % verticalLevels)

            # Sampling start time (year month day hour minute)
            f.write("%s\n" % self._model_start.strftime("%y %m %d %H %M"))

            # Sampling stop time (year month day hour minute)
            # The following would be the same as
            # model_end = self._model_start + datetime.timedelta(
            #     hours=self._num_hours)
            model_end = self._model_start + datetime.timedelta(
                hours=self._num_hours)
            f.write("%s\n" % model_end.strftime("%y %m %d %H %M"))

            # Sampling interval (type hour minute)
            # A type of 0 gives an average over the interval.
            sampling_interval_type = int(self.config("SAMPLING_INTERVAL_TYPE"))
            sampling_interval_hour = int(self.config("SAMPLING_INTERVAL_HOUR"))
            sampling_interval_min  = int(self.config("SAMPLING_INTERVAL_MIN"))
            #f.write("0 1 00\n")
            f.write("%d %d %d\n" % (sampling_interval_type, sampling_interval_hour, sampling_interval_min))

            # Number of pollutants undergoing deposition
            f.write("1\n") # only modeling PM2.5 for now

            # Particle diameter (um), density (g/cc), shape
            particle_diamater = self.config("PARTICLE_DIAMETER")
            particle_density  = self.config("PARTICLE_DENSITY")
            particle_shape    = self.config("PARTICLE_SHAPE")
            #f.write("1.0 1.0 1.0\n")
            f.write("%g %g %g\n" % ( particle_diamater, particle_density, particle_shape))


            # Dry deposition:
            #    deposition velocity (m/s),
            #    molecular weight (g/mol),
            #    surface reactivity ratio,
            #    diffusivity ratio,
            #    effective Henry's constant
            dry_dep_velocity    = self.config("DRY_DEP_VELOCITY")
            dry_dep_mol_weight  = self.config("DRY_DEP_MOL_WEIGHT")
            dry_dep_reactivity  = self.config("DRY_DEP_REACTIVITY")
            dry_dep_diffusivity = self.config("DRY_DEP_DIFFUSIVITY")
            dry_dep_eff_henry   = self.config("DRY_DEP_EFF_HENRY")
            #f.write("0.0 0.0 0.0 0.0 0.0\n")
            f.write("%g %g %g %g %g\n" % ( dry_dep_velocity, dry_dep_mol_weight, dry_dep_reactivity, dry_dep_diffusivity, dry_dep_eff_henry))

            # Wet deposition (gases):
            #     actual Henry's constant (M/atm),
            #     in-cloud scavenging ratio (L/L),
            #     below-cloud scavenging coefficient (1/s)
            wet_dep_actual_henry   = self.config("WET_DEP_ACTUAL_HENRY")
            wet_dep_in_cloud_scav    = self.config("WET_DEP_IN_CLOUD_SCAV")
            wet_dep_below_cloud_scav = self.config("WET_DEP_BELOW_CLOUD_SCAV")
            #f.write("0.0 0.0 0.0\n")
            f.write("%g %g %g\n" % ( wet_dep_actual_henry, wet_dep_in_cloud_scav, wet_dep_below_cloud_scav ))

            # Radioactive decay half-life (days)
            radioactive_half_life = self.config("RADIOACTIVE_HALF_LIVE")
            #f.write("0.0\n")
            f.write("%g\n" % radioactive_half_life)

            # Pollutant deposition resuspension constant (1/m)
            # non-zero requires the definition of a deposition grid
            f.write("0.0\n")

    def _write_setup_file(self, fires, emissions_file, setup_file, ninit_val, ncpus, tranche_num):
        # Advanced setup options
        # adapted from Robert's HysplitGFS Perl script

        khmax_val = int(self.config("KHMAX"))

        # pardump vars
        ndump_val = int(self.config("NDUMP"))
        ncycl_val = int(self.config("NCYCL"))
        dump_datetime = self._model_start + datetime.timedelta(hours=ndump_val)

        # emission cycle time
        qcycle_val =self.config("QCYCLE")

        # type of dispersion to use
        initd_val = int(self.config("INITD"))

        # set time step stuff
        tratio_val = self.config("TRATIO")
        delt_val = self.config("DELT")

        # set numpar (if 0 then set to num_fires * num_heights)
        # else set to value given (hysplit default of 500)
        num_fires = len(fires)
        num_heights = self.num_output_quantiles + 1
        numpar_val = int(self.config("NUMPAR"))
        num_sources = numpar_val
        if numpar_val == 0:
            num_sources = num_fires * num_heights

        # set maxpar. if 0 set to num_sources (ie, numpar) * 1000/ncpus
        # else set to value given (hysplit default of 10000)
        maxpar_val = int(self.config("MAXPAR"))
        max_particles = maxpar_val
        if maxpar_val == 0:
            max_particles = (num_sources * 1000) / ncpus

        # name of the particle input file (check for strftime strings)
        parinit = self.config("PARINIT")
        if "%" in parinit:
            parinit = self._model_start.strftime(parinit)
        if tranche_num is not None:
            parinit = parinit + '-' + str(tranche_num).zfill(2)


        # name of the particle output file (check for strftime strings)
        pardump = self.config("PARDUMP")
        if "%" in pardump:
            pardump = self._model_start.strftime(pardump)
        if tranche_num is not None:
            pardump = pardump + '-' + str(tranche_num).zfill(2)

        # conversion module
        ichem_val = int(self.config("ICHEM"))

        # minimum size in grid units of the meteorological sub-grid
        mgmin_val = int(self.config("MGMIN"))

        with open(setup_file, "w") as f:
            f.write("&SETUP\n")

            # conversion module
            f.write("  ICHEM = %d,\n" % ichem_val)

            # qcycle: the number of hours between emission start cycles
            f.write("  QCYCLE = %f,\n" % qcycle_val)

            # mgmin: default is 10 (from the hysplit user manual). however,
            #        once a run complained and said i need to reaise this
            #        variable to some value around what i have here
            f.write("  MGMIN = %d,\n" % mgmin_val)

            # maxpar: max number of particles that are allowed to be active at one time
            f.write("  MAXPAR = %d,\n" % max_particles)

            # numpar: number of particles (or puffs) permited than can be released
            #         during one time step
            f.write("  NUMPAR = %d,\n" % num_sources)

            # khmax: maximum particle duration in terms of hours after relase
            f.write("  KHMAX = %d,\n" % khmax_val)

            # delt: used to set time step integration interval (used along
            #       with tratio
            f.write("  DELT = %g,\n" % delt_val)
            f.write("  TRATIO = %g,\n" % tratio_val)

            # initd: # 0 - Horizontal and Vertical Particle
            #          1 - Horizontal Gaussian Puff, Vertical Top Hat Puff
            #          2 - Horizontal and Vertical Top Hat Puff
            #          3 - Horizontal Gaussian Puff, Vertical Particle
            #          4 - Horizontal Top-Hat Puff, Vertical Particle (default)
            f.write("  INITD = %d,\n" % initd_val)

            # make the 'smoke initizilaztion' files?
            # pinfp: particle initialization file (see also ninit)
            if ninit_val > 0:
                f.write("  PINPF = \"%s\",\n" % parinit)

            # ninit: (used along side parinit) sets the type of initialization...
            #        0 - no initialzation (even if files are present)
            #        1 = read parinit file only once at initialization time
            #        2 = check each hour, if there is a match then read those
            #            values in
            #        3 = like '2' but replace emissions instead of adding to
            #            existing particles
            f.write("  NINIT = %d,\n" % ninit_val)

            # pardump: particle output/dump file
            if self.config("MAKE_INIT_FILE"):
                pardump_dir = os.path.dirname(pardump)
                if not os.path.isdir(pardump_dir):
                    # Even though we check if the dir exists before calling
                    # os.makedirs, set exist_ok=True in case of race
                    # condition in multi-process mode.  (It's happened)
                    os.makedirs(pardump_dir, exist_ok=True)

                f.write("  POUTF = \"%s\",\n" % pardump)
                logging.info("Dumping particles to %s starting at %s every %s hours" % (pardump, dump_datetime, ncycl_val))

            # ndump: when/how often to dump a pardump file negative values
            #        indicate to just one create just one 'restart' file at
            #        abs(hours) after the model start
            # NOTE: negative hours do no actually appear to be supported, rcs)
            if self.config("MAKE_INIT_FILE"):
                f.write("  NDUMP = %d,\n" % ndump_val)

            # ncycl: set the interval at which time a pardump file is written
            #        after the 1st file (which is first created at
            #        T = ndump hours after the start of the model simulation
            if self.config("MAKE_INIT_FILE"):
                f.write("  NCYCL = %d,\n" % ncycl_val)

            # efile: the name of the emissions info (used to vary emission rate etc (and
            #        can also be used to change emissions time
            f.write("  EFILE = \"%s\",\n" % os.path.basename(emissions_file))

            f.write("&END\n")
