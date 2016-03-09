"""bluesky.dispersers.hysplit.defaults
"""

import os

# NOTE: executables are no longer configurable.  It is assumed that any
# executable upon which hysplit depends is in a directory in the search path.
# This is a security measure for when hysplit is executed via web requests.

# Ancillary data files (note: HYSPLIT4.9 balks if it can't find ASCDATA.CFG)
_bdyfiles_path = os.path.join(os.path.dirname(__file__), 'bdyfiles')
ASCDATA_FILE = os.path.join(_bdyfiles_path, 'ASCDATA.CFG')
LANDUSE_FILE = os.path.join(_bdyfiles_path, 'LANDUSE.ASC')
ROUGLEN_FILE = os.path.join(_bdyfiles_path, 'ROUGLEN.ASC')

# Program to convert raw HYSPLIT output to netCDF
CONVERT_HYSPLIT2NETCDF = True

# Height in meters where smoldering emissions should be injected into the model
SMOLDER_HEIGHT = 10.0

# Method of vertical motion calculation in HYSPLIT
# Choices: DATA, ISOB, ISEN, DENS, SIGMA, DIVERG, ETA
VERTICAL_METHOD = "DATA"

# Height in meters of the top of the model domain
TOP_OF_MODEL_DOMAIN = 30000.0

# List of vertical levels for output sampling grid
VERTICAL_LEVELS = [10]

# Factor for reducing the number of vertical emission levels
VERTICAL_EMISLEVELS_REDUCTION_FACTOR = 1

# User defined concentration grid option
USER_DEFINED_GRID = False
# CENTER_LATITUDE = 44.0
# CENTER_LONGITUDE = -121
# WIDTH_LONGITUDE = 138
# HEIGHT_LATITUDE = 62
# SPACING_LONGITUDE = 0.5
# SPACING_LATITUDE = 0.5

# computing grid around fire
COMPUTE_GRID = False
GRID_LENGTH = 2000 # km
# SPACING_LONGITUDE = 0.5
# SPACING_LATITUDE = 0.5

# Optimize (i.e. decrease) concentration grid resolution based on number of fires
OPTIMIZE_GRID_RESOLUTION = False
MAX_SPACING_LONGITUDE = 0.50
MAX_SPACING_LATITUDE = 0.50
FIRE_INTERVALS = [0, 100, 200, 500, 1000]

### HYSPLIT Setup variables

## Particle restart options

#  Location of particle initialization input files
DISPERSION_FOLDER = "./input/dispersion"

# conversion modules
#    0 - none
#    1 - matrix
#    2 - 10% / hour
#    3 - PM10 dust storm simulation
#    4 - Set concentration grid identical to the meteorology grid (not in GUI)
#    5 - Deposition Probability method
#    6 - Puff to Particle conversion (not in GUI)
#    7 - Surface water pollutant transport
ICHEM = 0

# NINIT: Read a particle initialization input file?
NINIT = 0

# name of the particle initialization input file
# NOTE: must be limited to 80 chars max (i think, rcs)
PINPF = "./input/dispersion/PARINIT"

# Stop processing if no particle initialization file is found and
# NINIT != 0
STOP_IF_NO_PARINIT = True

# Create a particle initialization input file
MAKE_INIT_FILE = False

# name of the particle initialization output file
# NOTES: must be limited to 80 chars max (i think, rcs)
#        also, MPI runs will append a .NNN at the end
#        based on the CPU number. subsequent restarts must
#        use the same number of CPUs as the original that
#        created the dump files. code will warn if there
#        are few files than CPUs but will ignore files
#        for cases when more files than CPUs.
POUTF = './input/dispersion/PARDUMP'

# Number of hours from the start of the simulation to write the particle
# initialization file (NOTE: unlike the comments in the v7 hysplit module,
# negative values do not actually appear to be supported as NDUMP must be
# greater than 0 for this to occur)
NDUMP = 0

# The repeat interval at which the particle initialization file will be
# written after NDUMP
NCYCL = 0

## ADVANCED Setup variable options

# Minimum size in grid units of the meteorological sub-grid
#         default is 10 (from the hysplit user manual). however,
#         once hysplit complained and said i need to raise this
#         variable to some value around 750...leaving w/default
#         but change if required.
MGMIN = 10

# Maximum length of a trajectory in hours
KHMAX = 72

# Number of hours between emission start cycles
QCYCLE = 1.0

# 0 - horizontal & vertical particle
# 1 - horizontal gaussian puff, vertical top hat puff
# 2 - horizontal & vertical top hat puff
# 3 - horizontal gaussian puff, verticle particle
# 4 - horizontal top hat puff, verticle particle
INITD = 0

# used to calculate the time step integration interval
TRATIO = 0.750
DELT = 0.0

# particle release limits. if 0 is provided then the values are calculated
# based on the number of sources: numpar = num_sources = num_fires*num_heights)
# and maxpar = numpar*1000/ncpus
NUMPAR = 500
MAXPAR = 10000

#
# MPI options
#
# This flag triggers MPI with multpile cores/processors on a single (local) node via MPICH2
MPI = False

# Number of processors/cores per HYSPLIT Process
NCPUS = 1

# Optional tranching of dispersion calculation using multiple HYSPLIT processes
# There are two options:
#  - Specify the number of processes (NPROCESSES) and let BlueSky determine
#    how many fires are input into each process
#  - Specify the number of fires per process (NFIRES_PER_PROCESS) and
#    let BlueSky determine how many processes need to be run, up to an
#    optional max (NPROCESSES_MAX).  The NFIRES_PER_PROCESS/NPROCESSES_MAX
#    option is ignored if NPROCESSES is set to 1 or greater
NPROCESSES = 1
NFIRES_PER_PROCESS = -1
NPROCESSES_MAX = -1

# Machines file (TODO: functionality for multiple nodes)
#MACHINEFILE = machines

#
# CONTROL vars:
#

# sampling interval type, hour & min (default 0 1 0)
# type of 0 gives the average over the interval
SAMPLING_INTERVAL_TYPE = 0
SAMPLING_INTERVAL_HOUR = 1
SAMPLING_INTERVAL_MIN  = 0

# particle stuff (1.0 use default hysplit values)
# diamater in micrometer, density in g/cc.
PARTICLE_DIAMETER = 1.0
PARTICLE_DENSITY = 1.0
PARTICLE_SHAPE = 1.0

# dry deposition vars (0.0 use default hysplit values)
# velocity is m/s and weight is g/mol.
DRY_DEP_VELOCITY = 0.0
DRY_DEP_MOL_WEIGHT = 0.0
DRY_DEP_REACTIVITY = 0.0
DRY_DEP_DIFFUSIVITY = 0.0
DRY_DEP_EFF_HENRY = 0.0

# wet deposition vars (0.0 use default hysplit values)
# in-cloud scav is L/L, below cloud is 1/s.
WET_DEP_ACTUAL_HENRY = 0.0
WET_DEP_IN_CLOUD_SCAV = 0.0
WET_DEP_BELOW_CLOUD_SCAV = 0.0

# radioactive decay half live in days (0.0 is default, ie: no decay)
RADIOACTIVE_HALF_LIVE = 0.0

del os
