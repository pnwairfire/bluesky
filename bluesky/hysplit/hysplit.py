"""bluesky.hysplit.hysplit

This code in this module was copied from BlueSky Framework, and modified
significantly.

TODO: acknowledge original authors (STI?)
"""

__author__      = "Joel Dubowy and others (unknown)"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__version__ = "0.1.0"

# import os.path
import logging
import os
import tempfile
# import math
# from datetime import timedelta
# import tarfile
# import threading
# import contextlib
# from shutil import copyfileobj

# from arlgridfile import ARLGridFile
# from hysplitIndexedDataLocation import IndexedDataLocation, CatalogIndexedData

# from glob import glob
# from kernel.context import Context
# from kernel.core import Process
# from kernel.utility import which
# from kernel.bs_datetime import BSDateTime,UTC
# from kernel.types import construct_type
# from kernel.log import SUMMARY
# from trajectory import Trajectory, TrajectoryMet
# from dispersion import Dispersion, DispersionMet

import hysplit_utils
import defaults

HYSPLIT_BINARY = "hycs_std"
HYSPLIT_MPI_BINARY = "hycm_std"
NCEA_EXECUTABLE = "ncea"
NCKS_EXECUTABLE = "ncks"
MPIEXEC = "mpiexec"
HYSPLIT2NETCDF_BINARY = "hysplit2netcdf"

class working_dir(object):
    def __enter__(self):
        self._original_dir = os.getcwd()
        self._working_dir = tempfile.mkdtemp()
        os.chdir(self._working_dir)

    def __exit__(self):
        os.chdir(self._original_dir)
        # TODO: delete self._working_dir or just let os clean it up ?

class HYSPLITDispersion(object):
    """ HYSPLIT Dispersion model

    HYSPLIT Concentration model version 4.9
    """

    def __init__(self, **config):
        self._config = config
        # TODO: determine which config options we'll support

    def __del__(self):
        # TODO: explicitly destroy self._working_dir ?
        pass

    def config(self, key):
        return self._config.get(key.lower(), getattr(self, key, None))

    def run(self, fires_manager, start, end):
        logging.info("Running the HYSPLIT49 Dispersion model")
        self.model_start = start
        self.model_end = end
        # TODO: make sure start and end are within
        # metmin(self.metInfo.dispersion_end, self.metInfo.met_end)
        dur = self.model_end - self.model_start
        self.hours_to_run = ((dur.days * 86400) + dur.seconds) / 3600

        self.gather_data(fires_manager)
        self.set_reduction_factor()
        filteredFires = list(self.filterFires())

        if(len(filteredFires) == 0):
            filteredFires = [self.generate_dummy_fire()]

        tranching_config = {
            'num_processes': self.config("NPROCESSES", int),
            'num_fires_per_process': self.config("NFIRES_PER_PROCESS", int),
            'num_processes_max': self.config("NPROCESSES_MAX", int)
        }

        # Note: organizing the fire sets is wasted computation if we end up
        # running only one process, but doing so before looking at the
        # NPROCESSES, NFIRES_PER_PROCESS, NPROCESSES_MAX config values allows
        # for more code to be encapsulated in hysplit_utils, which then allows
        # for greater testability.  (hysplit_utils.create_fire_sets could be
        # skipped if either NPROCESSES > 1 or NFIRES_PER_PROCESS > 1)
        filtered_fire_location_sets = hysplit_utils.create_fire_sets(filteredFires)
        num_fire_sets = len(filtered_fire_location_sets)
        num_processes = hysplit_utils.compute_num_processes(num_fire_sets,
            **tranching_config)
        self.log.debug('Parallel HYSPLIT? num_fire_sets=%s, %s -> num_processes=%s' %(
            num_fire_sets, ', '.join(['%s=%s'%(k,v) for k,v in tranching_config.items()]),
            num_processes
        ))

        with working_dir() as wdir:
            if 1 < num_processes:
                    # hysplit_utils.create_fire_tranches will log number of processes
                    # and number of fires each
                    self.run_parallel(context, num_processes, filtered_fire_location_sets)
            else:
                self.log.info("Running one HYSPLIT49 Dispersion model process")
                self.run_process(context, filteredFires)

            # DispersionData output
            dispersionData = construct_type("DispersionData")
            dispersionData["grid_filetype"] = "NETCDF"
            dispersionData["grid_filename"] = context.full_path(self.OUTPUT_FILE_NAME)
            dispersionData["parameters"] = {"pm25": "PM25"}
            dispersionData["start_time"] = self.model_start
            dispersionData["hours"] = self.hours_to_run
            self.fireInfo.dispersion = dispersionData
            self.set_output("fires", self.fireInfo)

            # TODO: Move to desired output location


    DUMMY_EMISSIONS = (
        "time", "heat", "pm25", "pm10",
        "co", "co2", "ch4", "nox",
        "nh3", "so2", "voc", "pm", "nmhc"
    )
    DUMMY_EMISSIONS_VALUE = 0.00001
    DUMMY_HOURS = 24
    DUMMY_PLUME_RISE_HOUR_VALUES = (0.00001, 0.00001, 0.00001)
    DUMMY_TIME_PROFILE_KEYS = [
        'area_fract', 'flame_profile', 'smolder_profile', 'residual_profile'
        ]

    def gather_data(self, fires_manager):
        # TODO: Iterate over all fires to gather required data,
        #  aggreagating over all fires (if possible)
        #  use self.config["start"] and self.config["end"]
        #  to determine dispserion time window, and then look at
        #  growth window(s) of each fire to fill in emissions for each
        #  fire spanning hysplit time window
        # TODO: determine set of arl fires by aggregating arl files
        #  specified per growth per fire, or expect global arl files
        #  specifications?  (if aggregating over fires, make sure they're
        #  conistent with met domain; if not, raise exception or run them
        #  separately...raising exception easier for now)
        for fire in fires_manager.fires:
            # TODO: ...
            for g in fire.growth:
                # TODO: ...
                pass


    def generate_dummy_fire(self):
        self.log.info("Generating dummy fire for HYSPLIT")
        from kernel.types import construct_type
        dummy_loc = construct_type("FireLocationData", "DUMMY_FIRE")
        dummy_loc['latitude'] = self.config("CENTER_LATITUDE", float)
        dummy_loc['longitude'] = self.config("CENTER_LONGITUDE", float)
        dummy_loc['area'] = 1
        dummy_loc['date_time'] = self.model_start

        dummy_loc['emissions'] =  construct_type("EmissionsData")
        for k in self.DUMMY_EMISSIONS:
            dummy_loc.emissions[k] = []
            for h in xrange(self.DUMMY_HOURS):  #self.hours_to_run):
                et = construct_type("EmissionsTuple")
                et.flame = self.DUMMY_EMISSIONS_VALUE
                et.smold = self.DUMMY_EMISSIONS_VALUE
                et.resid = self.DUMMY_EMISSIONS_VALUE
                dummy_loc.emissions[k].append(et)

        dummy_loc['plume_rise'] = construct_type("PlumeRise")
        dummy_loc.plume_rise.hours = []
        for h in xrange(self.DUMMY_HOURS):
            prh = construct_type("PlumeRiseHour", *self.DUMMY_PLUME_RISE_HOUR_VALUES)
            dummy_loc.plume_rise.hours.append(prh)
        dummy_loc['time_profile'] = construct_type("TimeProfileData")
        for k in self.DUMMY_TIME_PROFILE_KEYS:
            dummy_loc.time_profile[k] = [1.0 / self.DUMMY_HOURS] * self.DUMMY_HOURS
        return dummy_loc

    OUTPUT_FILE_NAME = "hysplit_conc.nc"

    def run_parallel(self, context, num_processes, filtered_fire_location_sets):
        runner = self
        class T(threading.Thread):
            def  __init__(self, context, fires):
                super(T, self).__init__()
                self.context = context
                self.fires = fires
                self.exc = None

            def run(self):
                try:
                    runner.run_process(self.context, self.fires)
                except Exception, e:
                    self.exc = e

        fire_tranches = hysplit_utils.create_fire_tranches(
            filtered_fire_location_sets, num_processes, logger=self.log)
        threads = []
        for nproc in xrange(len(fire_tranches)):
            fires = fire_tranches[nproc]
            _context = Context(os.path.join(context.workdir, str(nproc)))
            # Note: no need to set _context.basedir; it will be set to workdir
            self.log.info("Starting thread to run HYSPLIT on %d fires." % (len(fires)))
            t = T(_context, fires)
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

        #ncea_args = ["-y", "ttl", "-O"]
        ncea_args = ["-O","-v","PM25","-y","ttl"]
        ncea_args.extend(["%d/%s" % (i, self.OUTPUT_FILE_NAME) for i in  xrange(num_processes)])
        ncea_args.append(context.full_path(self.OUTPUT_FILE_NAME))
        context.execute(NCEA_EXECUTABLE, *ncea_args)

        ncks_args = ["-A","-v","TFLAG"]
        ncks_args.append("0/%s" % (self.OUTPUT_FILE_NAME))
        ncks_args.append(context.full_path(self.OUTPUT_FILE_NAME))
        context.execute(NCKS_EXECUTABLE, *ncks_args)

    def run_process(self, context, fires):
        # TODO: set all but context and fires as instance properties in self.run
        # so that they don't have to be passed into each call to run_process
        # The only things that change from call to call are context and fires

        for f in self.metInfo.files:
            context.link_file(f.filename)

        # Ancillary data files (note: HYSPLIT49 balks if it can't find ASCDATA.CFG).
        ASCDATA_FILE = self.config("ASCDATA_FILE")
        LANDUSE_FILE = self.config("LANDUSE_FILE")
        ROUGLEN_FILE = self.config("ROUGLEN_FILE")
        context.link_file(ASCDATA_FILE)
        context.link_file(LANDUSE_FILE)
        context.link_file(ROUGLEN_FILE)

        emissionsFile = context.full_path("EMISS.CFG")
        controlFile = context.full_path("CONTROL")
        setupFile = context.full_path("SETUP.CFG")
        messageFiles = [context.full_path("MESSAGE")]
        outputConcFile = context.full_path("hysplit.con")
        outputFile = context.full_path(self.OUTPUT_FILE_NAME)

        # Default value for NINIT for use in set up file.  0 equals no particle initialization
        ninit_val = "0"

        if self.config("READ_INIT_FILE", bool):
           parinit_file = self.config("DISPERSION_FOLDER") + "/PARINIT"

           if not context.file_exists(parinit_file):
              if self.config("STOP_IF_NO_PARINIT", bool):
                 msg = "Found no matching particle initialization files. Stop."
                 raise Exception(msg)
              else:
                 self.log.warn("No matching particle initialization file found; Using no particle initialization")
                 self.log.debug("Particle initialization file not found '%s'", parinit_file)
           else:
              context.link_file(parinit_file)
              self.log.info("Using particle initialization file %s" % parinit_file)
              ninit_val = "1"

        # Prepare for an MPI run
        if self.config("MPI", bool):
            NCPUS = self.config("NCPUS", int)
            self.log.info("Running MPI HYSPLIT with %s processors." % NCPUS)
            if NCPUS < 1:
                self.log.warn("Invalid NCPUS specified...resetting NCPUS to 1 for this run.")
                NCPUS = 1

            messageFiles = ["MESSAGE.%3.3i" % (i+1) for i in range(NCPUS)]
            pardumpFiles = ["PARDUMP.%3.3i" % (i+1) for i in range(NCPUS)]
            # TODO: either update the following checks for MPIEXEC and
            # SHYSPLIT_MPI_BINARY to try running with -v or -h option or
            # something similar,  or remove them
            # if not context.file_exists(MPIEXEC):
            #     msg = "Failed to find %s. Check MPIEXEC setting and/or your MPICH2 installation." % mpiexec
            #     raise AssertionError(msg)
            # if not context.file_exists(SHYSPLIT_MPI_BINARY):
            #     msg = "HYSPLIT MPI executable %s not found." % SHYSPLIT_MPI_BINARY
            #     raise AssertionError(msg)
            if self.config("READ_INIT_FILE", bool): # TODO: Finish MPI support for particle initialization
                self.log.warn("Particile initialization in BlueSky module not currently supported for MPI runs.")
        else:
            NCPUS = 1

        self.writeEmissions(fires, emissionsFile)
        self.writeControlFile(fires, controlFile, outputConcFile)
        self.writeSetupFile(fires, emissionsFile, setupFile, ninit_val, NCPUS)

        # Copy in the user_defined SETUP.CFG file or write a new one
        HYSPLIT_SETUP_FILE = self.config("HYSPLIT_SETUP_FILE")
        if HYSPLIT_SETUP_FILE != None:
            self.log.debug("Copying HYSPLIT SETUP file from %s" % (HYSPLIT_SETUP_FILE))
            config_setup_file = open(HYSPLIT_SETUP_FILE, 'rb')
            setup_file = open(setupFile, 'wb')
            copyfileobj(config_setup_file, setup_file)
            config_setup_file.close()
            setup_file.close()
        else:
            self.writeSetupFile(fires, emissionsFile, setupFile, ninit_val, NCPUS)

        # Run HYSPLIT
        if self.config("MPI", bool):
            context.execute(MPIEXEC, "-n", str(NCPUS), SHYSPLIT_MPI_BINARY)
        else:  # standard serial run
            context.execute(HYSPLIT_BINARY)

        if not os.path.exists(outputConcFile):
            msg = "HYSPLIT failed, check MESSAGE file for details"
            raise AssertionError(msg)

        if self.config('CONVERT_HYSPLIT2NETCDF'):
            self.log.info("Converting HYSPLIT output to NetCDF format: %s -> %s" % (outputConcFile, outputFile))
            context.execute(HYSPLIT2NETCDF_BINARY,
                "-I" + outputConcFile,
                "-O" + os.path.basename(outputFile),
                "-X1000000.0",  # Scale factor to convert from grams to micrograms
                "-D1",  # Debug flag
                "-L-1"  # Lx is x layers. x=-1 for all layers...breaks KML output for multiple layers
                )

            if not os.path.exists(outputFile):
                msg = "Unable to convert HYSPLIT concentration file to NetCDF format"
                raise AssertionError(msg)

        # TODO: config option to specify where to put output files
        # Archive data files
        context.archive_file(emissionsFile)
        context.archive_file(controlFile)
        context.archive_file(setupFile)
        for f in messageFiles:
            context.archive_file(f)
        if self.config("MAKE_INIT_FILE", bool):
            if self.config("MPI", bool):
                for f in pardumpFiles:
                    context.archive_file(f)
                    context.copy_file(context.full_path(f),self.config("OUTPUT_DIR"))
            else:
                context.archive_file(context.full_path("PARDUMP"))
                context.copy_file(context.full_path("PARDUMP"),self.config("OUTPUT_DIR") + "/PARDUMP_"+ self.config("DATE"))

    # Number of quantiles in vertical emissions allocation scheme
    NQUANTILES = 20

    def set_reduction_factor(self):
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
        self.reductionFactor = self.config("VERTICAL_EMISLEVELS_REDUCTION_FACTOR")
        self.reductionFactor = int(self.reductionFactor)

        # Ensure a valid reduction factor
        if self.reductionFactor > self.NQUANTILES:
            self.reductionFactor = self.NQUANTILES
            self.log.debug("VERTICAL_EMISLEVELS_REDUCTION_FACTOR reset to %s" % str(self.NQUANTILES))
        elif self.reductionFactor <= 0:
            self.reductionFactor = 1
            self.log.debug("VERTICAL_EMISLEVELS_REDUCTION_FACTOR reset to 1")
        while (self.NQUANTILES % self.reductionFactor) != 0:  # make sure factor evenly divides into the number of quantiles
            self.reductionFactor -= 1
            self.log.debug("VERTICAL_EMISLEVELS_REDUCTION_FACTOR reset to %s" % str(self.reductionFactor))

        self.num_output_quantiles = self.NQUANTILES/self.reductionFactor

        if self.reductionFactor != 1:
            self.log.info("Number of vertical emission levels reduced by factor of %s" % str(self.reductionFactor))
            self.log.info("Number of vertical emission quantiles will be %s" % str(self.num_output_quantiles))

    def filterFires(self):
        for fireLoc in self.fireInfo.locations():
            if fireLoc.time_profile is None:
                self.log.debug("Fire %s has no time profile data; skip...", fireLoc.id)
                continue

            if fireLoc.plume_rise is None:
                self.log.debug("Fire %s has no plume rise data; skip...", fireLoc.id)
                continue

            if fireLoc.emissions is None:
                self.log.debug("Fire %s has no emissions data; skip...", fireLoc.id)
                continue

            if fireLoc.emissions.sum("heat") < 1.0e-6:
                self.log.debug("Fire %s has less than 1.0e-6 total heat; skip...", fireLoc.id)
                continue

            yield fireLoc

    def writeEmissions(self, filteredFires, emissionsFile):
        # Note: HYSPLIT can accept concentrations in any units, but for
        # consistency with CALPUFF and other dispersion models, we convert to
        # grams in the emissions file.
        GRAMS_PER_TON = 907184.74

        # Conversion factor for fire size
        SQUARE_METERS_PER_ACRE = 4046.8726

        # A value slightly above ground level at which to inject smoldering
        # emissions into the model.
        SMOLDER_HEIGHT = self.config("SMOLDER_HEIGHT", float)

        with open(emissionsFile, "w") as emis:
            # HYSPLIT skips past the first two records, so these are for comment purposes only
            emis.write("emissions group header: YYYY MM DD HH QINC NUMBER\n")
            emis.write("each emission's source: YYYY MM DD HH MM DUR_HHMM LAT LON HT RATE AREA HEAT\n")

            # Loop through the timesteps
            for hour in range(self.hours_to_run):
                dt = self.model_start + timedelta(hours=hour)
                dt_str = dt.strftime("%y %m %d %H")

                num_fires = len(filteredFires)
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
                for fireLoc in filteredFires:
                    dummy = False

                    # Get some properties from the fire location
                    lat = fireLoc.latitude
                    lon = fireLoc.longitude

                    # Figure out what index (h) to use into our hourly arrays of data,
                    # based on the hour in our outer loop and the fireLoc's available
                    # data.
                    padding = fireLoc.date_time - self.model_start
                    padding_hours = ((padding.days * 86400) + padding.seconds) / 3600
                    num_hours = min(len(fireLoc.emissions.heat), len(fireLoc.plume_rise.hours))
                    h = hour - padding_hours

                    # If we don't have real data for the given timestep, we apparently need
                    # to stick in dummy records anyway (so we have the correct number of sources).

                    if h < 0 or h >= num_hours:
                        self.log.debug("Fire %s has no emissions for hour %s", fireLoc.id, hour)
                        noEmis += 1
                        dummy = True

                    area_meters = 0.0
                    smoldering_fraction = 0.0
                    pm25_injected = 0.0
                    if not dummy:
                        # Extract the fraction of area burned in this timestep, and
                        # convert it from acres to square meters.
                        area = fireLoc.area * fireLoc.time_profile.area_fract[h]
                        area_meters = area * SQUARE_METERS_PER_ACRE

                        smoldering_fraction = fireLoc.plume_rise.hours[h].smoldering_fraction
                        # Total PM2.5 emitted at this timestep (grams)
                        pm25_emitted = fireLoc.emissions.pm25[h].sum() * GRAMS_PER_TON
                        # Total PM2.5 smoldering (not lofted in the plume)
                        pm25_injected = pm25_emitted * smoldering_fraction

                    entrainment_fraction = 1.0 - smoldering_fraction

                    # We don't assign any heat, so the PM2.5 mass isn't lofted
                    # any higher.  This is because we are assigning explicit
                    # heights from the plume rise.
                    heat = 0.0

                    # Inject the smoldering fraction of the emissions at ground level
                    # (SMOLDER_HEIGHT represents a value slightly above ground level)
                    height_meters = SMOLDER_HEIGHT

                    # Write the smoldering record to the file
                    record_fmt = "%s 00 0100 %8.4f %9.4f %6.0f %7.2f %7.2f %15.2f\n"
                    emis.write(record_fmt % (dt_str, lat, lon, height_meters, pm25_injected, area_meters, heat))

                    #for pct in range(0, 100, 5):
                    for pct in range(0, 100, self.reductionFactor*5):
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

                            lower_height = fireLoc.plume_rise.hours[h]["percentile_%03d" % (pct)]
                            #upper_height = fireLoc.plume_rise.hours[h]["percentile_%03d" % (pct + 5)]
                            upper_height = fireLoc.plume_rise.hours[h]["percentile_%03d" % (pct + (self.reductionFactor*5))]
                            if self.reductionFactor == 1:
                                height_meters = (lower_height + upper_height) / 2.0  # original approach
                            else:
                                 height_meters = upper_height # top-edge approach
                            # Total PM2.5 entrained (lofted in the plume)
                            pm25_entrained = pm25_emitted * entrainment_fraction
                            # Inject the proper fraction of the entrained PM2.5 in each quantile gap.
                            #pm25_injected = pm25_entrained * 0.05  # 1/20 = 0.05
                            pm25_injected = pm25_entrained * (float(self.reductionFactor)/float(self.num_output_quantiles))

                        # Write the record to the file
                        emis.write(record_fmt % (dt_str, lat, lon, height_meters, pm25_injected, area_meters, heat))

                if noEmis > 0:
                    self.log.debug("%d of %d fires had no emissions for hour %d", noEmis, num_fires, hour)


    VERTICAL_CHOICES = {
        "DATA": 0,
        "ISOB": 1,
        "ISEN": 2,
        "DENS": 3,
        "SIGMA": 4,
        "DIVERG": 5,
        "ETA": 6
    }
    def getVerticalMethod(self):
        # Vertical motion choices:

        VERTICAL_METHOD = self.config("VERTICAL_METHOD")
        try:
            verticalMethod = self.VERTICAL_CHOICES[VERTICAL_METHOD]
        except KeyError:
            verticalMethod = self.VERTICAL_CHOICES["DATA"]

        return verticalMethod

    def writeControlFile(self, filteredFires, controlFile, concFile):
        num_fires = len(filteredFires)
        num_heights = self.num_output_quantiles + 1  # number of quantiles used, plus ground level
        num_sources = num_fires * num_heights

        # An arbitrary height value.  Used for the default source height
        # in the CONTROL file.  This can be anything we want, because
        # the actual source heights are overridden in the EMISS.CFG file.
        sourceHeight = 15.0

        verticalMethod = getVerticalMethod(self)

        # Height of the top of the model domain
        modelTop = self.config("TOP_OF_MODEL_DOMAIN", float)

        #modelEnd = self.model_start + timedelta(hours=self.hours_to_run)

        # Build the vertical Levels string
        verticalLevels = self.config("VERTICAL_LEVELS")
        levels = [int(x) for x in verticalLevels.split()]
        numLevels = len(levels)
        verticalLevels = " ".join(str(x) for x in levels)

        # Warn about multiple sampling grid levels and KML/PNG image generation
        if numLevels > 1:
            self.log.warn("KML and PNG images will be empty since more than 1 vertical level is selected")

        if self.config("USER_DEFINED_GRID", bool):
            # User settings that can override the default concentration grid info
            self.log.info("User-defined sampling/concentration grid invoked")
            centerLat = self.config("CENTER_LATITUDE", float)
            centerLon = self.config("CENTER_LONGITUDE", float)
            widthLon = self.config("WIDTH_LONGITUDE", float)
            heightLat = self.config("HEIGHT_LATITUDE", float)
            spacingLon = self.config("SPACING_LONGITUDE", float)
            spacingLat = self.config("SPACING_LATITUDE", float)
        else:
            # Calculate output concentration grid parameters.
            # Ensure the receptor spacing divides nicely into the grid width and height,
            # and that the grid center will be a receptor point (i.e., nx, ny will be ODD).
            self.log.info("Automatic sampling/concentration grid invoked")

            projection = self.metInfo.met_domain_info.domainID
            grid_spacing_km = self.metInfo.met_domain_info.dxKM
            lat_min = self.metInfo.met_domain_info.lat_min
            lat_max = self.metInfo.met_domain_info.lat_max
            lon_min = self.metInfo.met_domain_info.lon_min
            lon_max = self.metInfo.met_domain_info.lon_max
            lat_center = (lat_min + lat_max) / 2
            spacing = grid_spacing_km / ( 111.32 * math.cos(lat_center*math.pi/180.0) )
            if projection == "LatLon":
                spacing = grid_spacing_km  # degrees

            # Build sampling grid parameters in scaled integer form
            SCALE = 100
            lat_min_s = int(lat_min*SCALE)
            lat_max_s = int(lat_max*SCALE)
            lon_min_s = int(lon_min*SCALE)
            lon_max_s = int(lon_max*SCALE)
            spacing_s = int(spacing*SCALE)

            lat_count = (lat_max_s - lat_min_s) / spacing_s
            lat_count += 1 if lat_count % 2 == 0 else 0  # lat_count should be odd
            lat_max_s = lat_min_s + ((lat_count-1) * spacing_s)

            lon_count = (lon_max_s - lon_min_s) / spacing_s
            lon_count += 1 if lon_count % 2 == 0 else 0  # lon_count should be odd
            lon_max_s = lon_min_s + ((lon_count-1) * spacing_s)
            self.log.info("HYSPLIT grid DIMENSIONS will be %s by %s" % (lon_count, lat_count))

            spacingLon = float(spacing_s)/SCALE
            spacingLat = spacingLon
            centerLon = float((lon_min_s + lon_max_s) / 2) / SCALE
            centerLat = float((lat_min_s + lat_max_s) / 2) / SCALE
            widthLon = float(lon_max_s - lon_min_s) / SCALE
            heightLat = float(lat_max_s - lat_min_s) / SCALE

        # Decrease the grid resolution based on number of fires
        if self.config("OPTIMIZE_GRID_RESOLUTION", bool):
            self.log.info("Grid resolution adjustment option invoked")
            minSpacingLon = spacingLon
            minSpacingLat = spacingLat
            maxSpacingLon = self.config("MAX_SPACING_LONGITUDE", float)
            maxSpacingLat = self.config("MAX_SPACING_LATITUDE", float)
            fireIntervals = self.config("FIRE_INTERVALS")
            intervals = sorted([int(x) for x in fireIntervals.split()])

            # Maximum grid spacing cannot be smaller than the minimum grid spacing
            if maxSpacingLon < minSpacingLon:
                maxSpacingLon = minSpacingLon
                self.log.debug("maxSpacingLon > minSpacingLon...longitude grid spacing will not be adjusted")
            if maxSpacingLat < minSpacingLat:
                maxSpacingLat = minSpacingLat
                self.log.debug("maxSpacingLat > minSpacingLat...latitude grid spacing will not be adjusted")

            # Throw out negative intervals
            intervals = [x for x in intervals if x >= 0]

            if len(intervals) == 0:
                intervals = [0,num_fires]
                self.log.debug("FIRE_INTERVALS had no values >= 0...grid spacing will not be adjusted")

            # First bin should always start with zero
            if intervals[0] != 0:
                intervals.insert(0,0)
                self.log.debug("Zero added to the beginning of FIRE_INTERVALS list")

            # must always have at least 2 intervals
            if len(intervals) < 2:
                intervals = [0,num_fires]
                self.log.debug("Need at least two FIRE_INTERVALS...grid spacing will not be adjusted")

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
                self.log.debug("Lon,Lat grid spacing for interval %d adjusted to %f,%f" % (interval,spacingLon,spacingLat))
            self.log.info("Lon/Lat grid spacing for %d fires will be %f,%f" % (num_fires,spacingLon,spacingLat))

        # Note: Due to differences in projections, the dimensions of this
        #       output grid are conservatively large.
        self.log.info("HYSPLIT grid CENTER_LATITUDE = %s" % centerLat)
        self.log.info("HYSPLIT grid CENTER_LONGITUDE = %s" % centerLon)
        self.log.info("HYSPLIT grid HEIGHT_LATITUDE = %s" % heightLat)
        self.log.info("HYSPLIT grid WIDTH_LONGITUDE = %s" % widthLon)
        self.log.info("HYSPLIT grid SPACING_LATITUDE = %s" % spacingLat)
        self.log.info("HYSPLIT grid SPACING_LONGITUDE = %s" % spacingLon)

        with open(controlFile, "w") as f:
            # Starting time (year, month, day hour)
            f.write(self.model_start.strftime("%y %m %d %H") + "\n")

            # Number of sources
            f.write("%d\n" % num_sources)

            # Source locations
            for fireLoc in filteredFires:
                for height in range(num_heights):
                    f.write("%9.3f %9.3f %9.3f\n" % (fireLoc.latitude, fireLoc.longitude, sourceHeight))

            # Total run time (hours)
            f.write("%04d\n" % self.hours_to_run)

            # Method to calculate vertical motion
            f.write("%d\n" % verticalMethod)

            # Top of model domain
            f.write("%9.1f\n" % modelTop)

            # Number of input data grids (met files)
            f.write("%d\n" % len(self.metInfo.files))
            # Directory for input data grid and met file name
            for info in self.metInfo.files:
                f.write("./\n")
                f.write("%s\n" % os.path.basename(info.filename))

            # Number of pollutants = 1 (only modeling PM2.5 for now)
            f.write("1\n")
            # Pollutant ID (4 characters)
            f.write("PM25\n")
            # Emissions rate (per hour) (Ken's code says "Emissions source strength (mass per second)" -- which is right?)
            f.write("0.001\n")
            # Duration of emissions (hours)
            f.write(" %9.3f\n" % self.hours_to_run)
            # Source release start time (year, month, day, hour, minute)
            f.write("%s\n" % self.model_start.strftime("%y %m %d %H %M"))

            # Number of simultaneous concentration grids
            f.write("1\n")

            # NOTE: The size of the output concentration grid is specified
            # here, but it appears that the ICHEM=4 option in the SETUP.CFG
            # file may override these settings and make the sampling grid
            # correspond to the input met grid instead...
            # But Ken's testing seems to indicate that this is not the case...

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
            f.write("%s\n" % self.model_start.strftime("%y %m %d %H %M"))
            # Sampling stop time (year month day hour minute)
            f.write("%s\n" % self.model_end.strftime("%y %m %d %H %M"))
            # Sampling interval (type hour minute)
            f.write("0 1 00\n") # Sampling interval:  type hour minute.  A type of 0 gives an average over the interval.

            # Number of pollutants undergoing deposition
            f.write("1\n") # only modeling PM2.5 for now

            # Particle diameter (um), density (g/cc), shape
            f.write("1.0 1.0 1.0\n")

            # Dry deposition:
            #    deposition velocity (m/s),
            #    molecular weight (g/mol),
            #    surface reactivity ratio,
            #    diffusivity ratio,
            #    effective Henry's constant
            f.write("0.0 0.0 0.0 0.0 0.0\n")

            # Wet deposition (gases):
            #     actual Henry's constant (M/atm),
            #     in-cloud scavenging ratio (L/L),
            #     below-cloud scavenging coefficient (1/s)
            f.write("0.0 0.0 0.0\n")

            # Radioactive decay half-life (days)
            f.write("0.0\n")

            # Pollutant deposition resuspension constant (1/m)
            f.write("0.0\n")

    def writeSetupFile(self, filteredFires, emissionsFile, setupFile, ninit_val, ncpus):
        # Advanced setup options
        # adapted from Robert's HysplitGFS Perl script

        khmax_val = int(self.config("KHMAX"))
        ndump_val = int(self.config("NDUMP"))
        ncycl_val = int(self.config("NCYCL"))
        dump_datetime = self.model_start + timedelta(hours=ndump_val)

        num_fires = len(filteredFires)
        num_heights = self.num_output_quantiles + 1
        num_sources = num_fires * num_heights

        max_particles = (num_sources * 1000) / ncpus

        with open(setupFile, "w") as f:
            f.write("&SETUP\n")

            # ichem: i'm only really interested in ichem = 4 in which case it causes
            #        the hysplit concgrid to be roughly the same as the met grid
            # -- But Ken says it may not work as advertised...
            #f.write("  ICHEM = 4,\n")

            # qcycle: the number of hours between emission start cycles
            f.write("  QCYCLE = 1.0,\n")

            # mgmin: a run once complained and said i need to reaise this variable to
            #        some value around what i have here...it has something to do with
            #        the minimum size (in grid units) of the met sub-grib.
            f.write("  MGMIN = 750,\n")

            # maxpar: max number of particles that are allowed to be active at one time
            f.write("  MAXPAR = %d,\n" % max_particles)

            # numpar: number of particles (or puffs) permited than can be released
            #         during one time step
            f.write("  NUMPAR = %d,\n" % num_sources)

            # khmax: maximum particle duration in terms of hours after relase
            f.write("  KHMAX = %d,\n" % khmax_val)

            # initd: # 0 - Horizontal and Vertical Particle
            #          1 - Horizontal Gaussian Puff, Vertical Top Hat Puff
            #          2 - Horizontal and Vertical Top Hat Puff
            #          3 - Horizontal Gaussian Puff, Vertical Particle
            #          4 - Horizontal Top-Hat Puff, Vertical Particle (default)
            f.write("  INITD = 1,\n")

            # make the 'smoke initizilaztion' files?
            # pinfp: particle initialization file (see also ninit)
            if self.config("READ_INIT_FILE", bool):
               f.write("  PINPF = \"PARINIT\",\n")

            # ninit: (used along side pinpf) sets the type of initialization...
            #          0 - no initialzation (even if files are present)
            #          1 = read pinpf file only once at initialization time
            #          2 = check each hour, if there is a match then read those values in
            #          3 = like '2' but replace emissions instead of adding to existing
            #              particles
            f.write("  NINIT = %s,\n" % ninit_val)

            # poutf: particle output/dump file
            if self.config("MAKE_INIT_FILE", bool):
                f.write("  POUTF = \"PARDUMP\",\n")
                self.log.info("Dumping particles to PARDUMP starting at %s every %s hours" % (dump_datetime, ncycl_val))

            # ndump: when/how often to dump a poutf file negative values indicate to
            #        just one  create just one 'restart' file at abs(hours) after the
            #        model start
            if self.config("MAKE_INIT_FILE", bool):
                f.write("  NDUMP = %d,\n" % ndump_val)

            # ncycl: set the interval at which time a pardump file is written after the
            #        1st file (which is first created at T = ndump hours after the
            #        start of the model simulation
            if self.config("MAKE_INIT_FILE", bool):
                f.write("  NCYCL = %d,\n" % ncycl_val)

            # efile: the name of the emissions info (used to vary emission rate etc (and
            #        can also be used to change emissions time
            f.write("  EFILE = \"%s\",\n" % os.path.basename(emissionsFile))

            f.write("&END\n")
