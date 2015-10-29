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

# Path to pre-generated version of SETUP.CFG to be used instead of creating
# that file dynamically.
#HYSPLIT_SETUP_FILE = ${PACKAGE_DIR}/Example_SETUP.CFG

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

# Optimize (i.e. decrease) concentration grid resolution based on number of fires
OPTIMIZE_GRID_RESOLUTION = False
MAX_SPACING_LONGITUDE = 0.50
MAX_SPACING_LATITUDE = 0.50
FIRE_INTERVALS = [0, 100, 200, 500, 1000]
#
# Particle restart options
#
#  Location of particle initialization input files
DISPERSION_FOLDER = "./input/dispersion"

# Read a particle initialization input file
READ_INIT_FILE = False

# Make a particle initialization input file
MAKE_INIT_FILE = False

# Stop processing if no particle initialization file is found
STOP_IF_NO_PARINIT = True

#
# HYSPLIT Setup variables
#
# Number of hours from the start of the simulation to write the particle initialization file
NDUMP = 24

# The repeat interval at which the particle initialization file will be written after NDUMP
NCYCL = 24

# Maximum length of a trajectory in hours
KHMAX = 72

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

