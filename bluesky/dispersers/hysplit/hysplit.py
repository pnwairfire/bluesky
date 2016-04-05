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
                to control if and how to read in PINPF file

            HYSPLIT_SETUP_CFG is no longer supported. instead include
                the SETUP.CFG variable one wishes to set in the .ini
                list of supported vars:
                NCYCL, NDUMP, KHMAX, NINIT, INITD, PINPF, POUTF,
                QCYCLE, TRATIO, DELT, NUMPAR, MAXPAR, MGMIN and
                ICHEM

                PINPF & POUTF can both handle strftime strings in
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
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

__version__ = "0.2.0"

import copy
import logging
import math
import os
import shutil
# import tarfile
import threading
from datetime import timedelta

from bluesky.exceptions import BlueSkyConfigurationError

from .. import (
    DispersionBase, GRAMS_PER_TON, SQUARE_METERS_PER_ACRE
)

from . import defaults, hysplit_utils

__all__ = [
    'HYSPLITDispersion'
]

class HYSPLITDispersion(DispersionBase):
    """ HYSPLIT Dispersion model

    HYSPLIT Concentration model version 4.9

    TODO: determine which config options we'll support
    """
    BINARIES = {
        'HYSPLIT': "hycs_std",
        'HYSPLIT_MPI': "hycm_std",
        'NCEA': "ncea",
        'NCKS': "ncks",
        'MPI': "mpiexec",
        'HYSPLIT2NETCDF': "hysplit2netcdf"
    }
    DEFAULTS = defaults

    # Note: 'PHASES' and TIMEPROFILE_FIELDS defined in HYSPLITDispersion

    def __init__(self, met_info, **config):
        super(HYSPLITDispersion, self).__init__(met_info, **config)
        self._set_met_info(copy.deepcopy(met_info))

    def _required_growth_fields(self):
        return ('timeprofile', 'plumerise')

    def _run(self, wdir):
        """Runs hysplit

        args:
         - wdir -- working directory
        """
        self._create_dummy_fire_if_necessary()
        self._set_reduction_factor()
        fire_sets, num_processes  = self._compute_tranches()

        if 1 < num_processes:
                # hysplit_utils.create_fire_tranches will log number of processes
                # and number of fires each
                self._run_parallel(num_processes, fire_sets, wdir)
        else:
            self._run_process(self._fires, wdir)

        # Note: DispersionBase.run will add directory, start_time,
        #  and num_hours to the response dict
        return {
            "output": {
                "grid_filetype": "NETCDF",
                "grid_filename": self.OUTPUT_FILE_NAME,
                "parameters": {"pm25": "PM25"},
                "grid_parameters": self._grid_params
            },
            "met_info": self._met_info
        }

    def _set_met_info(self, met_info):
        # TODO: move validation code into common module pyairfire.met.validation ?
        self._met_info = {}

        if met_info.get('grid'):
            self._met_info['grid'] = met_info['grid']
        # The grid fields, 'domain', 'boundary', and 'grid_spacing_km' can be
        # defined either in the met object or in the hsyplit config. Expections
        # will be raised downstream if not defined in either place

        # hysplit just needs the name
        self._met_info['files'] = set()
        if not met_info.get('files'):
            raise ValueError("Met info lacking arl file information")
        for met_file in met_info.pop('files'):
            if not met_file.get('file'):
                raise ValueError("ARL file not defined for specified date range")
            if not os.path.exists(met_file['file']):
                raise ValueError("ARL file does not exist: {}".format(
                    met_file['file']))
            self._met_info['files'].add(met_file['file'])
        self._met_info['files'] = list(self._met_info['files'])

    def _create_dummy_fire_if_necessary(self):
        # TODO: create a dummy fire no matter what (in case whatever fires
        #   are in the list are filtered by hysplit?)
        if not self._fires:
            self._fires = [self._generate_dummy_fire()]

    DUMMY_EMISSIONS = (
        "pm25", "pm10", "co", "co2", "ch4", "nox",
        "nh3", "so2", "voc", "pm", "nmhc"
    )
    DUMMY_EMISSIONS_VALUE = 0.00001
    DUMMY_HOURS = 24
    # TODO: make sure these dummy plumerise values don't have unexpected consequences
    DUMMY_PLUMERISE_HOUR = dict({'percentile_%03d'%(5*e): 0.05*e for e in range(21)},
        smolder_fraction=0.0)

    def _generate_dummy_fire(self):
        """Returns dummy fire formatted like
        """
        logging.info("Generating dummy fire for HYSPLIT")
        f = Fire(
            # let fire autogenerate id
            area=1,
            latitude=self.config("CENTER_LATITUDE"),
            longitude=self.config("CENTER_LONGITUDE"),
            utc_offset=0, # since plumerise and timeprofile will have utc keys
            plumerise={},
            timeprofile={},
            emissions={
                p: {
                    e: self.DUMMY_EMISSIONS_VALUE for e in self.DUMMY_EMISSIONS
                } for p in self.PHASES
            }
        )
        for i in range(self._num_hours):
            dt = self._model_start + timedelta(hours=hour)
            f['plumerise'][dt] = self.DUMMY_PLUMERISE_HOUR
            f['timeprofile'][dt] = {f: 1.0 / float(self._num_hours) for d in self.TIMEPROFILE_FIELDS}

        return f

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

        self.num_output_quantiles = self.NQUANTILES/self._reduction_factor

        if self._reduction_factor != 1:
            logging.info("Number of vertical emission levels reduced by factor of %s" % str(self._reduction_factor))
            logging.info("Number of vertical emission quantiles will be %s" % str(self.num_output_quantiles))

    def _compute_tranches(self):
        tranching_config = {
            'num_processes': self.config("NPROCESSES"),
            'num_fires_per_process': self.config("NFIRES_PER_PROCESS"),
            'num_processes_max': self.config("NPROCESSES_MAX")
        }

        # Note: organizing the fire sets is wasted computation if we end up
        # running only one process, but doing so before looking at the
        # NPROCESSES, NFIRES_PER_PROCESS, NPROCESSES_MAX config values allows
        # for more code to be encapsulated in hysplit_utils, which then allows
        # for greater testability.  (hysplit_utils.create_fire_sets could be
        # skipped if either NPROCESSES > 1 or NFIRES_PER_PROCESS > 1)
        fire_sets = hysplit_utils.create_fire_sets(self._fires)
        num_fire_sets = len(fire_sets)
        num_processes = hysplit_utils.compute_num_processes(num_fire_sets,
            **tranching_config)
        logging.debug('Parallel HYSPLIT? num_fire_sets=%s, %s -> num_processes=%s' %(
            num_fire_sets, ', '.join(['%s=%s'%(k,v) for k,v in tranching_config.items()]),
            num_processes
        ))
        return fire_sets, num_processes

    OUTPUT_FILE_NAME = "hysplit_conc.nc"

    def _run_parallel(self, num_processes, fire_sets, working_dir):
        runner = self
        class T(threading.Thread):
            def  __init__(self, fires, working_dir):
                super(T, self).__init__()
                self.fires = fires
                self.working_dir = working_dir
                self.exc = None

            def run(self):
                try:
                    runner._run_process(self.fires, self.working_dir)
                except Exception, e:
                    self.exc = e

        fire_tranches = hysplit_utils.create_fire_tranches(
            fire_sets, num_processes)
        threads = []
        for nproc in xrange(len(fire_tranches)):
            fires = fire_tranches[nproc]
            # Note: no need to set _context.basedir; it will be set to workdir
            logging.info("Starting thread to run HYSPLIT on %d fires." % (len(fires)))
            t = T(fires, os.path.join(working_dir, str(nproc)))
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
        # sum together all the PM25 fields then append the TFLAG field from
        # one of the individual runs (they're all the same)
        # using run 0 as it should always be present regardless of how many
        # processes were used....
        # prevents ncea from adding all the TFLAGs together and mucking up the
        # date

        output_file = os.path.join(working_dir, self.OUTPUT_FILE_NAME)

        #ncea_args = ["-y", "ttl", "-O"]
        ncea_args = ["-O","-v","PM25","-y","ttl"]
        ncea_args.extend(["%d/%s" % (i, self.OUTPUT_FILE_NAME) for i in  xrange(num_processes)])
        ncea_args.append(output_file)
        self._execute(self.BINARIES['NCEA'], *ncea_args, working_dir=working_dir)

        ncks_args = ["-A","-v","TFLAG"]
        ncks_args.append("0/%s" % (self.OUTPUT_FILE_NAME))
        ncks_args.append(output_file)
        self._execute(self.BINARIES['NCKS'], *ncks_args, working_dir=working_dir)

    def _run_process(self, fires, working_dir):
        logging.info("Running one HYSPLIT49 Dispersion model process")
        # TODO: set all but fires and working_dir as instance properties in self.run
        # so that they don't have to be passed into each call to _run_process
        # The only things that change from call to call are context and fires

        for f in self._met_info['files']:
            os.symlink(f, os.path.join(working_dir, os.path.basename(f)))

        # Create sym links to ancillary data files (note: HYSPLIT49 balks
        # if it can't find ASCDATA.CFG).
        os.symlink(self.config("ASCDATA_FILE"), os.path.join(working_dir, 'ASCDATA.CFG'))
        os.symlink(self.config("LANDUSE_FILE"), os.path.join(working_dir, 'LANDUSE.ASC'))
        os.symlink(self.config("ROUGLEN_FILE"), os.path.join(working_dir, 'ROUGLEN.ASC'))

        emissions_file = os.path.join(working_dir, "EMISS.CFG")
        control_file = os.path.join(working_dir, "CONTROL")
        setup_file = os.path.join(working_dir, "SETUP.CFG")
        message_files = [os.path.join(working_dir, "MESSAGE")]
        output_conc_file = os.path.join(working_dir, "hysplit.con")
        output_file = os.path.join(working_dir, self.OUTPUT_FILE_NAME)

        # NINIT: sets how particle init file is to be used
        #  0 = no particle initialization file read (default)
        #  1 = read pinpf file only once at initialization time
        #  2 = check each hour, if there is a match then read those values in
        #  3 = like '2' but replace emissions instead of adding to existing
        #      particles
        ninit = self.config("NINIT")
        ninit_val = 0
        if ninit != None:
            ninit_val = int(ninit)

        # need an input file if ninit_val > 0
        if ninit_val > 0:
             # name of pardump input file, pinpf (check for strftime strings)
            pinpf = self.config("PINPF")
            if "%" in pinpf:
                pinpf = self._model_start.strftime(pinpf)
            parinitFiles = [ "%s" % pinpf ]

            # if an MPI run need to create the full list of expected files
            # based on the number of CPUs
            if self.config("MPI",bool):
                NCPUS = self.config("NCPUS", int)
                parinitFiles = ["%s.%3.3i" % ( pinpf, (i+1)) for i in range(NCPUS)]

            # loop over parinitFiles check if exists.
            # for MPI runs check that all files exist...if any in the list
            # don't exist raise exception if STOP_IF_NO_PARINIT is True
            # if STOP_IF_NO_PARINIT is False and all/some files don't exist,
            # set ninit_val to 0 and issue warning.
            for f in parinitFiles:
                if not context.file_exists(f):
                    if self.config("STOP_IF_NO_PARINIT", bool):
                        msg = "Matching particle init file, %s, not found. Stop." % f
                        raise Exception(msg)
                    else:
                        msg = "No matching particle initialization file, %s, found; Using no particle initialization" % f
                        self.log.warn(msg)
                        self.log.debug(msg)
                        ninit_val = 0
                    self.log.info("Using particle initialization file %s" % f)

        # Prepare for run ... get pardump name just in case needed
        poutf = self.config("POUTF")
        if "%" in poutf:
            poutf = self._model_start.strftime(poutf)
        pardumpFiles = [ "%s" % poutf ]

        # If MPI run
        if self.config("MPI"):
            NCPUS = self.config("NCPUS")
            logging.info("Running MPI HYSPLIT with %s processors." % NCPUS)
            if NCPUS < 1:
                logging.warn("Invalid NCPUS specified...resetting NCPUS to 1 for this run.")
                NCPUS = 1

            message_files = ["MESSAGE.%3.3i" % (i+1) for i in range(NCPUS)]

            # name of the pardump files (one for each CPU)
            if self.config("MAKE_INIT_FILE"):
                pardumpFiles = ["%s.%3.3i" % ( poutf, (i+1)) for i in range(NCPUS)]

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

        self._write_emissions(emissions_file)
        self._write_control_file(control_file, output_conc_file)
        self._write_setup_file(emissions_file, setup_file, ninit_val, NCPUS)

        try:
            # Run HYSPLIT
            if self.config("MPI"):
                self._execute(self.BINARIES['MPI'], "-n", str(NCPUS), self.BINARIES['HYSPLIT_MPI'], working_dir=working_dir)
            else:  # standard serial run
                self._execute(self.BINARIES['HYSPLIT'], working_dir=working_dir)

            if not os.path.exists(output_conc_file):
                msg = "HYSPLIT failed, check MESSAGE file for details"
                raise AssertionError(msg)
            self._archive_file(output_conc_file)

            if self.config('CONVERT_HYSPLIT2NETCDF'):
                logging.info("Converting HYSPLIT output to NetCDF format: %s -> %s" % (output_conc_file, output_file))
                self._execute(self.BINARIES['HYSPLIT2NETCDF'],
                    "-I" + output_conc_file,
                    "-O" + os.path.basename(output_file),
                    "-X1000000.0",  # Scale factor to convert from grams to micrograms
                    "-D1",  # Debug flag
                    "-L-1",  # Lx is x layers. x=-1 for all layers...breaks KML output for multiple layers
                    working_dir=working_dir
                )

                if not os.path.exists(output_file):
                    msg = "Unable to convert HYSPLIT concentration file to NetCDF format"
                    raise AssertionError(msg)
            self._archive_file(output_file)

        finally:
            # Archive input files
            self._archive_file(emissions_file)
            self._archive_file(control_file)
            self._archive_file(setup_file)

            # Archive data files
            for f in message_files:
                self._archive_file(f)
            if self.config("MAKE_INIT_FILE"):
                for f in pardumpFiles:
                    self._archive_file(f)
                    #shutil.copy2(os.path.join(working_dir, f), self._run_output_dir)

    def _write_emissions(self, emissions_file):
        # A value slightly above ground level at which to inject smoldering
        # emissions into the model.
        smolder_height = self.config("SMOLDER_HEIGHT")

        with open(emissions_file, "w") as emis:
            # HYSPLIT skips past the first two records, so these are for comment purposes only
            emis.write("emissions group header: YYYY MM DD HH QINC NUMBER\n")
            emis.write("each emission's source: YYYY MM DD HH MM DUR_HHMM LAT LON HT RATE AREA HEAT\n")

            # Loop through the timesteps
            for hour in range(self._num_hours):
                dt = self._model_start + timedelta(hours=hour)
                dt_str = dt.strftime("%y %m %d %H")

                num_fires = len(self._fires)
                #num_heights = 21 # 20 quantile gaps, plus ground level
                num_heights = self.num_output_quantiles + 1
                num_sources = num_fires * num_heights

                # TODO: What is this and what does it do?
                # A reasonable guess would be that it means a time increment of 1 hour
                qinc = 1

                # Write the header line for this timestep
                emis.write("%s %02d %04d\n" % (dt_str, qinc, num_sources))

                noEmis = 0

                # Loop through the fire locations
                for fire in self._fires:
                    dummy = False

                    # Get some properties from the fire location
                    lat = fire.latitude
                    lon = fire.longitude

                    # If we don't have real data for the given timestep, we apparently need
                    # to stick in dummy records anyway (so we have the correct number of sources).
                    if not fire.plumerise or not fire.timeprofile:
                        logging.debug("Fire %s has no emissions for hour %s", fire.id, hour)
                        noEmis += 1
                        dummy = True
                    else:
                        local_dt = dt + timedelta(hours=fire.utc_offset)
                        plumerise_hour = fire.plumerise.get(local_dt)
                        timeprofile_hour = fire.timeprofile.get(local_dt)

                    area_meters = 0.0
                    smoldering_fraction = 0.0
                    pm25_injected = 0.0
                    if not dummy:
                        # Extract the fraction of area burned in this timestep, and
                        # convert it from acres to square meters.
                        # TODO: ????? WHAT TIME PROFILE VALUE TO USE ?????
                        area = fire.area * timeprofile_hour['area_fraction']
                        area_meters = area * SQUARE_METERS_PER_ACRE

                        smoldering_fraction = plumerise_hour['smolder_fraction']

                        # Compute the total PM2.5 emitted at this timestep (grams) by
                        # multiplying the phase-specific total emissions by the
                        # phase-specific hourly fractions for this hour to get the
                        # hourly emissions by phase for this hour, and then summing
                        # the three values to get the total emissions for this hour
                        # TODO: use fire.timeprofiled_emissions[local_dt]['PM25']
                        pm25_emitted = sum([
                            timeprofile_hour[p]*fire.emissions[p].get('PM25', 0.0)
                                for p in self.PHASES
                        ])
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

                    #for pct in range(0, 100, 5):
                    for pct in range(0, 100, self._reduction_factor*5):
                        height_meters = 0.0
                        pm25_injected = 0.0

                        if not dummy:
                            # Loop through the heights (20 quantiles of smoke density)
                            # For the unreduced case, we loop through 20 quantiles, but we have
                            # 21 quantile-edge measurements.  So for each
                            # quantile gap, we need to find a point halfway
                            # between the two edges and inject 1/20th of the
                            # total emissions there.

                            # KJC optimization...
                            # Reduce the number of vertical emission levels by a reduction factor
                            # and place the appropriate fraction of emissions at each level.
                            # ReductionFactor MUST evenly divide into the number of quantiles

                            lower_height = plumerise_hour["percentile_%03d" % (pct)]
                            #upper_height = plumerise_hour["percentile_%03d" % (pct + 5)]
                            upper_height = plumerise_hour["percentile_%03d" % (pct + (self._reduction_factor*5))]
                            if self._reduction_factor == 1:
                                height_meters = (lower_height + upper_height) / 2.0  # original approach
                            else:
                                 height_meters = upper_height # top-edge approach
                            # Total PM2.5 entrained (lofted in the plume)
                            pm25_entrained = pm25_emitted * entrainment_fraction
                            # Inject the proper fraction of the entrained PM2.5 in each quantile gap.
                            #pm25_injected = pm25_entrained * 0.05  # 1/20 = 0.05
                            pm25_injected = pm25_entrained * (float(self._reduction_factor)/float(self.num_output_quantiles))

                        # Write the record to the file
                        emis.write(record_fmt % (dt_str, lat, lon, height_meters, pm25_injected, area_meters, heat))

                if noEmis > 0:
                    logging.debug("%d of %d fires had no emissions for hour %d", noEmis, num_fires, hour)


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

    def _write_control_file(self, control_file, concFile):
        num_fires = len(self._fires)
        num_heights = self.num_output_quantiles + 1  # number of quantiles used, plus ground level
        num_sources = num_fires * num_heights

        # An arbitrary height value.  Used for the default source height
        # in the CONTROL file.  This can be anything we want, because
        # the actual source heights are overridden in the EMISS.CFG file.
        sourceHeight = 15.0

        verticalMethod = self._get_vertical_method()

        # Height of the top of the model domain
        modelTop = self.config("TOP_OF_MODEL_DOMAIN")

        #modelEnd = self._model_start + timedelta(hours=self._num_hours)

        # Build the vertical Levels string
        levels = self.config("VERTICAL_LEVELS")
        numLevels = len(levels)
        verticalLevels = " ".join(str(x) for x in levels)

        # If not specified, projection is assumed to be 'LatLon'
        is_deg = (self.config('projection') or 'LatLon') == 'LatLon'

        # Warn about multiple sampling grid levels and KML/PNG image generation
        if numLevels > 1:
            logging.warn("KML and PNG images will be empty since more than 1 vertical level is selected")

        if self.config("USER_DEFINED_GRID"):
            # This supports BSF config settings
            # User settings that can override the default concentration grid info
            logging.info("User-defined sampling/concentration grid invoked")
            grid_params = {
                "center_latitude": self.config("CENTER_LATITUDE"),
                "center_longitude": self.config("CENTER_LONGITUDE"),
                "height_latitude": self.config("HEIGHT_LATITUDE"),
                "width_longitude": self.config("WIDTH_LONGITUDE"),
                "spacing_longitude": self.config("SPACING_LONGITUDE"),
                "spacing_latitude": self.config("SPACING_LATITUDE")
            }
            # BSF assumed lat/lng if USER_DEFINED_GRID; this support km spacing
            if not is_deg:
                grid_params["spacing_longitude"] /= hysplit_utils.km_per_deg_lng(
                    grid_params["center_latitude"])
                grid_params["spacing_latitude"] /= hysplit_utils.KM_PER_DEG_LAT

        elif self.config('grid'):
            grid_params = hysplit_utils.grid_params_from_grid(
                self.config('grid'), self._met_info)

        elif self.config('compute_grid'):
            if len(self._fires) != 1:
                # TODO: support multiple fires
                raise ValueError("Option to compute grid only supported for "
                    "runs with one fire")
            if (not self.config('spacing_latitude')
                    or not self.config('spacing_longitude')):
                raise BlueSkyConfigurationError("Config settings "
                    "'spacing_latitude' and 'spacing_longitude' required "
                    "to compute hysplit grid")
            grid_params = hysplit_utils.square_grid_from_lat_lng(
                self._fires[0]['latitude'], self._fires[0]['longitude'],
                self.config('spacing_latitude'), self.config('spacing_longitude'),
                self.config('grid_length'), input_spacing_in_degrees=is_deg)

        elif self._met_info.get('grid'):
            grid_params = hysplit_utils.grid_params_from_grid(
                self._met_info['grid'], self._met_info)

        else:
            raise BlueSkyConfigurationError("Specify hysplit dispersion grid")

        logging.debug("grid_params: %s", grid_params)

        self._grid_params = grid_params # to include in self._run's return data

        # To minimize change in the following code, set aliases
        centerLat =  grid_params["center_latitude"]
        centerLon = grid_params["center_longitude"]
        widthLon = grid_params["width_longitude"]
        heightLat = grid_params["height_latitude"]
        spacingLon = grid_params["spacing_longitude"]
        spacingLat = grid_params["spacing_latitude"]

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
            for fire in self._fires:
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
            model_end = self._model_start + timedelta(hours=self._num_hours)
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

    def _write_setup_file(self, emissions_file, setup_file, ninit_val, ncpus):
        # Advanced setup options
        # adapted from Robert's HysplitGFS Perl script

        khmax_val = int(self.config("KHMAX"))

        # pardump vars
        ndump_val = int(self.config("NDUMP"))
        ncycl_val = int(self.config("NCYCL"))
        dump_datetime = self._model_start + timedelta(hours=ndump_val)

        # emission cycle time
        qcycle_val =self.config("QCYCLE")

        # type of dispersion to use
        initd_val = int(self.config("INITD"))

        # set time step stuff
        tratio_val = self.config("TRATIO")
        delt_val = self.config("DELT")

        # set numpar (if 0 then set to num_fires * num_heights)
        # else set to value given (hysplit default of 500)
        num_fires = len(self._fires)
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
        pinpf = self.config("PINPF")
        if "%" in pinpf:
            pinpf = self._model_start.strftime(pinpf)

        # name of the particle output file (check for strftime strings)
        poutf = self.config("POUTF")
        if "%" in poutf:
            poutf = self._model_start.strftime(poutf)

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
                f.write("  PINPF = \"%s\",\n" % pinpf)

            # ninit: (used along side pinpf) sets the type of initialization...
            #        0 - no initialzation (even if files are present)
            #        1 = read pinpf file only once at initialization time
            #        2 = check each hour, if there is a match then read those
            #            values in
            #        3 = like '2' but replace emissions instead of adding to
            #            existing particles
            f.write("  NINIT = %d,\n" % ninit_val)

            # poutf: particle output/dump file
            if self.config("MAKE_INIT_FILE"):
                f.write("  POUTF = \"%s\",\n" % poutf)
                self.log.info("Dumping particles to %s starting at %s every %s hours" % (poutf, dump_datetime, ncycl_val))

            # ndump: when/how often to dump a poutf file negative values
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
