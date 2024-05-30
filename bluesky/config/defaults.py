"""bluesky.config.defaults"""

import copy
import os

__all__ = [
    "DEFAULTS",
    "to_lowercase_keys"
]

_REPO_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
_HYSPLIT_DISP_BDYFILES_PATH = os.path.join(_REPO_ROOT_DIR,
    'dispersers/hysplit/bdyfiles')
_HYSPLIT_TRAJ_BDYFILES_PATH = os.path.join(_REPO_ROOT_DIR,
    'trajectories/hysplit/bdyfiles')
_VSMOKE_IMAGES_PATH = os.path.join(_REPO_ROOT_DIR,
    'dispersers/vsmoke/images')

_DEFAULTS = {
    "skip_failed_fires": True,
    "skip_failed_sources": False,
    "statuslogging": {
        "enabled": False,
        "api_endpoint": None,
        "api_key": None,
        "api_secret": None,
        "process": None,
        "domain": None
    },
    "input": {
        "input_file_failure_tolerance": 'partial',
        # We need to default 'wait' to an empty dict, since an empty dict
        # indicates that we aren't waiting (which is the default behavior)
        "wait": {}, # {"strategy": None,"time": None,"max_attempts": None},
    },
    "load": {
        "sources": []
        # Each source has some subset of the following defined, but
        # there are no defaults to be defined here
        #  'name'
        #  'format'
        #  'type'
        #  'start'
        #  'end'
        #  'skip_failures'
        #  "wait": None, #{"strategy": None,"time": None,"max_attempts": None}
        #  "saved_copy_file"
        #  "saved_copy_events_file"
        # BSF
        #  "omit_nulls"
        #  "timeprofile_file"
        #  "load_consumption"
        #  "load_emissions"
        #  "area_units"
        #  "consumption_units"
        # File Sourcees
        #  'file'*** -- *required* for each file type source-- file containing fire data; e.g. '/path/to/fires.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)
        #  'events_file'*** -- *optional* for each file type source-- file containing fire events data; e.g. '/path/to/fire_events.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)
        # API sources
        #  'endpoint'
        #  'key'
        #  'secret'
        #  'key_param'
        #  'auth_protocol'
        #  'request_timeout'
        #  'query'

    },
    "merge": {
        "skip_failures": False
    },
    "filter": {
        "skip_failures": False
        # The following filter-specific sub-dicts have to be commented out
        # in the defaults, since each one's presence/absence determines whether
        # or not the filter is run.  There are no default values anyway
        # for the filter-specific options
        #   "area": {"min": None, "max": None}
        #   "time": {"start": None, "end": None}
        #   "location": {
        #     "boundary": {
        #       "sw": { "lat":None, "lng": None},
        #       "ne": { "lat":None, "lng": None}
        #     }
        #   }
        #   "<any other field>": {  # e.g. "country"
        #     "include": None,
        #     "exclude": None,
        #     "scope": "active_area"  # options: "active_area", "location"
        #     "tolerance": "any"  # options: "any", "all"
        #   },
    },
    "ecoregion": {
        "lookup_implementation": "ogr",
        "try_nearby_on_failure": False,
        "skip_failures": True,
        "default": None
    },
    "fuelbeds": {
        "skip_failures": False,

        # The following defaults are defined in the fccsmap package,
        # so they could be removed from here
        "ignored_fuelbeds": ['0', '900'],
        "ignored_percent_resampling_threshold": 99.9,
        "insignificance_threshold": 10.0,
        "max_fuelbed_count_threshold": 5,
        "no_sampling": False,
        "sampling_radius_km": 1.0,
        "sampling_radius_factors": None,
        "use_all_grid_cells": False,

        # fccs_version only comes into play if files aren't specified
        "fccs_fuelload_tile_sets": [], # each fileset is a dict with 'directory' and optionally 'index_shapefile'
        "fccs_fuelload_files": [],
        "fccs_version": "2",

        # Allow summed fuel percentages to be between 99.5% and 100.5%
        "total_pct_threshold": 0.5
    },
    "fuelmoisture":{
        # multiple models
        "models": ["nfdrs"],
        "use_defaults": False,
        "defaults_profile": None,
        "skip_failures": True,
        "nfdrs": {},
        "wims": {
            "url": "https://www.wfas.net/archive/www.fs.fed.us/land/wfas/archive/%Y/%m/%d/fdr_obs.dat",
            "data_dir": None # defaults to tmp folder
        }
    },
    "consumption": {
        "fuel_loadings": {},
        "scale_with_estimated_fuelload": False,
        "scale_with_estimated_consumption": False,
        "precomputed": {
            "enabled": False,
            "run_consume_on_failure": True
        },
        "summarize_fuel_loadings": False,
        "consume_settings": {
            # TODO: Confirm with Susan P, Susan O. to confirm that these
            #    burn-type specific settings (defaults and synonyms) are
            #    correct, and that none are missing
            'natural': {},
            'activity': {
                'slope': {
                    # percent, from 1 to 100;  consume package defaults to 5%
                    'defaults': {
                        'rx': 5,
                        'wildfire': 5,
                        'other': 5,
                    },
                },
                'windspeed': {
                    # consume package defaults to 5mph
                    'defaults': {
                        'rx': 6,
                        'wildfire': 6,
                        'other': 6,
                    },
                    # TODO: is 'max_wind' a valid synonym? or 'min_wind_aloft'?
                },
                'days_since_rain': {
                    'defaults': {
                        'rx': 10,
                        'wildfire': 10,
                        'other': 10,
                    },
                    'synonyms': ['rain_days'] # TODO: confirm
                },
                'fuel_moisture_10hr_pct': {
                    # consume package defaults to 50%
                    'defaults': {
                        'rx': 50,
                        'wildfire': 50,
                        'other': 50,
                    },
                    'synonyms': ['moisture_10hr'] # TODO: confirm
                },
                'length_of_ignition': {
                    # in minutes
                    'defaults': {
                        'rx': 120,
                        'wildfire': 120,
                        'other': 120,
                    },
                },
                'fm_type': {
                    # consume package defaults to 'MEAS-Th'
                    'defaults': {
                        'rx': 'MEAS-Th',
                        'wildfire': 'MEAS-Th',
                        'other': 'MEAS-Th',
                    },
                }
            },
            'all': {
                'fuel_moisture_1000hr_pct': {
                    'defaults': {
                        'rx': 35,
                        'wildfire': 15,
                        'other': 15,
                    },
                    'synonyms': ['moisture_1khr'] # TODO: confirm
                },
                'fuel_moisture_duff_pct': {
                    'defaults': {
                        'rx': 100,
                        'wildfire': 40,
                        'other': 40,
                    },
                    'synonyms': ['moisture_duff'] # TODO: confirm
                },
                'fuel_moisture_litter_pct': {
                    'defaults': {
                        'rx': 22,
                        'wildfire': 10,
                        'other': 10,
                    },
                    'synonyms': ['moisture_litter'] # TODO: confirm
                },
                'canopy_consumption_pct': {
                    'defaults': {
                        'rx': 0,
                        'wildfire': 0,
                        'other': 0,
                    },
                    # TDOO: is 'canopy' a valid synonym
                },
                'shrub_blackened_pct': {
                    'defaults': {
                        'rx': 50,
                        'wildfire': 50,
                        'other': 50,
                    },
                    # TODO: is 'shrub' a valid synonym
                },
                'pile_blackened_pct': {
                    'defaults': {
                        'rx': 0,
                        'wildfire': 0,
                        'other': 0,
                    },
                },
                'duff_pct_available': {
                    'defaults': {
                        'rx': 5,
                        'wildfire': 10,
                        'other': 10,
                    },
                },
                'sound_cwd_pct_available': {
                    'defaults': {
                        'rx': 5,
                        'wildfire': 10,
                        'other': 10,
                    },
                },
                'rotten_cwd_pct_available': {
                    'defaults': {
                        'rx': 5,
                        'wildfire': 10,
                        'other': 10,
                    },
                }
            }
        }
    },
    "emissions": {
        # Note that 'efs' is deprecated, and so is not listed here
        "model": "prichard-oneill",
        "include_emissions_details": False,
        "include_emissions_factors": False,
        "species": [],
        "fuel_loadings": {},
        "ubc-bsf-feps": {
            "working_dir": None,
            "delete_working_dir_if_no_error": True
        }
    },
    "growth": {
        "model": "persistence",
        # The "persistence" config must be set to None, since it may be either
        # a single object or an array of objects.  Defining it here as one
        # and then setting it as the other in the run's config file
        # results in a config merge error.
        "persistence": None
        # The fields in each persistence config object are:
        #     "date_to_persist" - defaults to 'today'
        #     "days_to_persist" - defaults to 1
        #     "daily_percentages" -  defaults to [100]
        #     "truncate" - defaults to false
        #     "start_day" - defaults to null
        #     "end_day" - defaults to null
        # 'days_to_persist' and 'daily_percentages' can't both be specified.
        # in any single config object. If neither is specified,
        # 'days_to_persist' (defaulted to 1) is used.
    },
    "findmetdata": {
        "met_root_dir": None,
        # We need to default time_window empty, since it will be used
        # if it has keys, even if the first and last hours are None
        "time_window": {}, # {"first_hour": None,"last_hour": None}

        # We need to default 'wait' to an empty dict, since an empty dict
        # indicates that we aren't waiting (which is the default behavior)
        "wait": {}, # {"strategy": None,"time": None,"max_attempts": None},

        "met_format": "arl",
        "arl": {
            # The following defaults are defined in the met package
            # TODO: should we comment them out here and leave the "arl"
            #    sub-config as an empty dict
            "accepted_forecasts": None,
            "index_filename_pattern": "arl12hrindex.csv",
            "max_days_out": 4
        },
        "skip_failures": False
    },
    "localmet": {
        # The following default is defined in the met package,
        # but we need to define it here so that the code doesn't fail
        "time_step": 1,
        "skip_failures": True,
        "working_dir": None,
        "delete_working_dir_if_no_error": True
    },
    "timeprofile": {
        "hourly_fractions": None,
        "model": "default",
        "ubc-bsf-feps": {
            "interpolation_type": 1,
            "normalize": True,
            "working_dir": None,
            "delete_working_dir_if_no_error": True
        }
    },

    "plumerise": {
        # Options: 'feps', 'sev', 'sev-feps'
        "model": "feps",
        "working_dir": None,
        "delete_working_dir_if_no_error": True,
        # Note: feps and sev specific configs are usd by 'sev-feps' model
        "feps": {
            "load_heat": False
            # The following defaults are defined in the plumerise
            # package, so we won't set them here
            # "feps_weather_binary": "feps_weather",
            # "feps_plumerise_binary": "feps_plumerise",
            # "plume_top_behavior": "auto",
        },
        "sev": {
            # The following defaults are defined in the plumerise
            # package, so we won't set them here
            # "alpha": 0.24
            # "beta": 170
            # "ref_power": 1e6
            # "gamma": 0.35
            # "delta": 0.6
            # "ref_n": 2.5e-4
            # "gravity": 9.8
            # "plume_bottom_over_top": 0.5
        },
        "sev-feps": {} # no config specific to sev-feps
    },
    "extrafiles": {
        "sets": [],
        "dest_dir": None,
        "emissionscsv": {
            "filename": None,
            # '{utc_offset}' results in whatever utc_offset was set to in
            # the input data (which might or might not have a colon)
            "date_time_format": "%Y-%m-%dT%H:%M:%S{utc_offset}"
        },
        "firescsvs": {
            "fire_locations_filename": "fire_locations.csv",
            "fire_events_filename": "fire_events.csv",
            "date_time_format": "%Y%m%d"
        },
        "smokeready": {
            # - PT filenames require datestamps
            # - FIPS does not appear to matter for the CMAQ runs,
            #   so we default to not performing a lookup.
            "ptinv_filename": "ptinv-{today:%Y%m%d%H}.ida",
            "ptday_filename": "ptday-{today:%Y%m%d%H}.ems95",
            "pthour_filename": "pthour-{today:%Y%m%d%H}.ems95",
            "separate_smolder": True,
            "write_ptinv_totals": True,
            "write_ptday_file": True,
            "use_fips": False
        },
    },
    "trajectories": {
        "model": "hysplit",
        "start": None,
        "num_hours": 24, # run time
        "output_dir": None,
        "working_dir": None,
        "delete_working_dir_if_no_error": True,
        "handle_existing": "fail",
        "hysplit": {
            "binary": 'hyts_std-v5.2.3',
            "start_hours": [0],
            "heights": [10, 100, 1000],
            "vertical_motion": 0, # 0 = from met file
            "top_of_model_domain": 10000,  # trajectories end above this
            "output_file_name": "tdump",
            "json_indent": None,
            "json_file_name": "hysplit-trajectories.json",
            "geojson_file_name": "hysplit-trajectories.geojson",
            "setup_file_params": {
                 "tm_tpot": 1,
                 "tm_tamb": 1,
                 "tm_rain": 1,
                 "tm_mixd": 1,
                 "tm_relh": 1,
                 "tm_dswf": 1,
                 "tm_terr": 0,
                 "kmsl": 0
            },
            "static_files": {
                "ASCDATA_FILE": os.path.join(_HYSPLIT_TRAJ_BDYFILES_PATH, 'ASCDATA.CFG'),
                "LANDUSE_FILE": os.path.join(_HYSPLIT_TRAJ_BDYFILES_PATH, 'LANDUSE.ASC'),
                "ROUGLEN_FILE": os.path.join(_HYSPLIT_TRAJ_BDYFILES_PATH, 'ROUGLEN.ASC'),
                "TERRAIN_FILE": os.path.join(_HYSPLIT_TRAJ_BDYFILES_PATH, 'TERRAIN.ASC')
            }
        }
    },
    "dispersion": {
        "model": "hysplit",
        "start": None,
        "num_hours": None,
        "output_dir": None,
        "working_dir": None,
        "delete_working_dir_if_no_error": True,
        "handle_existing": "fail",
        # As with hysplit grid configuration, below, there are no default
        # plume merge parameters, and the presence/absence
        # of plume_merge config (nonempty vs. empty dict) is used in
        # the logic in the code. So, leave fields commented out
        "plume_merge": {
            # "grid": {
            #     "spacing": None,
            #     # the region within which to merge plumes
            #     "boundary": {
            #         "sw": { "lat":None, "lng": None},
            #         "ne": { "lat":None, "lng": None}
            #     }
            # }
        },
        "hysplit": {
            "emissions_split": {
                "enabled": False,
                "target_pm25": 10.0,  # (specified in ug/m^3)
                "min_pm25": None  # (specified in ug/m^3)
            },
            "binaries": {},
            "skip_invalid_fires": False,

            # NOTE: executables are no longer configurable.  It is assumed that any
            # executable upon which hysplit depends is in a directory in the search path.
            # This is a security measure for when hysplit is executed via web requests.

            ## Grid

            # Note about the grid:  There are three ways to specify the dispersion grid.
            # If USER_DEFINED_GRID is set to true, hysplit will expect BlueSky framework's
            # user defined grid settings ('CENTER_LATITUDE', 'CENTER_LONGITUDE',
            # 'WIDTH_LONGITUDE', 'HEIGHT_LATITUDE', 'SPACING_LONGITUDE', and
            # 'SPACING_LONGITUDE').  Otherwise, it will look in 'config' > 'dispersion' >
            # 'hysplit' > 'grid' for 'boundary', 'spacing', and 'domain' fields.  If not
            # defined, it will look for 'boundary', 'spacing', and 'domain' in the top level
            # 'met' object.

            # User defined concentration grid option
            "USER_DEFINED_GRID": False,
            "CENTER_LATITUDE": None,
            "CENTER_LONGITUDE": None,
            "WIDTH_LONGITUDE": None,
            "HEIGHT_LATITUDE": None,

            # *required* if either COMPUTE_GRID or USER_DEFINED_GRID is true
            "SPACING_LONGITUDE": None,
            "SPACING_LATITUDE": None,
            "projection": "LatLon",

            # There are no default 'grid' parameter, and the presence/absence
            # of a grid definition (nonempty vs. empty grid dict) is used in
            # the logic in the code. So, leave grid fields commented out
            "grid": {
                # "spacing": None,
                # "domain": None,
                # "boundary": {
                #   "sw": { "lat":None, "lng": None},
                #   "ne": { "lat":None, "lng": None}
                # }
            },

            # computing grid around fire
            "COMPUTE_GRID": False, # Program to convert raw HYSPLIT output to netCDF
            "GRID_LENGTH": 2000, # km

            # Optimize (i.e. decrease) concentration grid resolution based on number of fires
            "OPTIMIZE_GRID_RESOLUTION": False,
            "MAX_SPACING_LONGITUDE": 0.50,
            "MAX_SPACING_LATITUDE": 0.50,

            ## Resource Files

            # Ancillary data files (note: HYSPLIT4.9 balks if it can't find ASCDATA.CFG)
            #  The code will default to using
            "ASCDATA_FILE": os.path.join(_HYSPLIT_DISP_BDYFILES_PATH, 'ASCDATA.CFG'),
            "LANDUSE_FILE": os.path.join(_HYSPLIT_DISP_BDYFILES_PATH, 'LANDUSE.ASC'),
            "ROUGLEN_FILE": os.path.join(_HYSPLIT_DISP_BDYFILES_PATH, 'ROUGLEN.ASC'),


            ## Other

            "archive_tranche_files": False,
            "archive_pardump_files": False,

            "ensure_dummy_fire": True,

            "CONVERT_HYSPLIT2NETCDF": True,
            "output_file_name": "hysplit_conc.nc",

            # default height to inject smoldering emissions
            # NOTE: is adjusted by smolder_fraction (calculated elsewhere) or
            #       adjusted to an an arbitrary constant for all sources
            #       as defined below
            "SMOLDER_HEIGHT": 10.0,

            # if False use calculated smolder_fraction else use constant
            # defined below
            "USE_CONST_SMOLDERING_FRACTION": False,

            # if USE_CONST_SMOLDERING_FRACTION is True then set a constant
            # value to determine amount lofted. 
            #     0.0 =  all is lofted 
            #     1.0 = none is lofted
            # NOTE: ONLY WORKS IN HYSPLIT CURRENTLY (not in smokeready/CMAQ)
            "SMOLDERING_FRACTION_CONST": 0.0,

            # Height in meters of the top of the model domain
            "TOP_OF_MODEL_DOMAIN": 10000.0,

            # List of vertical levels for output sampling grid
            "VERTICAL_LEVELS": [100],

            # Factor for reducing the number of vertical emission levels
            "VERTICAL_EMISLEVELS_REDUCTION_FACTOR": 1,

            # Factor for subhour emissions interval
            # sub-hour emission interval. should be an integer value of
            # 1 (hourly - default), 2 (30 min), 3 (20 min), 4 (15 min),
            #                       5 (12 min), 6 (10 min), 10 (6 min)
            #                    or 12 (5 min).
            "SUBHOUR_EMISSIONS_REDUCTION_INTERVAL": 1,

            # Emissions rate
            "EMISSIONS_RATE": 0.001,

            # Method of vertical motion calculation in HYSPLIT
            # Choices: DATA, ISOB, ISEN, DENS, SIGMA, DIVERG, ETA
            "VERTICAL_METHOD": "DATA",

            ## HYSPLIT Setup variables

            # Location of particle initialization input files
            "DISPERSION_FOLDER": "./input/dispersion",

            # conversion modules
            #    0 - none
            #    1 - matrix
            #    2 - 10% / hour
            #    3 - PM10 dust storm simulation
            #    4 - Set concentration grid identical to the meteorology grid (not in GUI)
            #    5 - Deposition Probability method
            #    6 - Puff to Particle conversion (not in GUI)
            #    7 - Surface water pollutant transport
            "ICHEM": 0,

            "FIRE_INTERVALS": [0, 100, 200, 500, 1000],

            # name of the particle initialization input file
            # NOTE: must be limited to 80 chars max (i think, rcs)
            "PARINIT": "./input/dispersion/PARINIT",

            "NINIT": 0,
            # Stop processing if no particle initialization file is found and NINIT != 0
            "STOP_IF_NO_PARINIT": True,

            # Create a particle initialization input file
            "MAKE_INIT_FILE": False,

            # name of the particle initialization output file
            # NOTES: must be limited to 80 chars max (i think, rcs)
            #        also, MPI runs will append a .NNN at the end
            #        based on the CPU number. subsequent restarts must
            #        use the same number of CPUs as the original that
            #        created the dump files. code will warn if there
            #        are few files than CPUs but will ignore files
            #        for cases when more files than CPUs.
            "PARDUMP": './input/dispersion/PARDUMP',

            # Number of hours from the start of the simulation to write the particle
            # initialization file (NOTE: unlike the comments in the v7 hysplit module,
            # negative values do not actually appear to be supported as NDUMP must be
            # greater than 0 for this to occur)
            "NDUMP": 0, # TODO: should this be 24 ?

            # The repeat interval at which the particle initialization file will be
            # written after NDUMP
            "NCYCL": 0, # TODO: should this be 24 ?

            ## ADVANCED Setup variable options

            # Minimum size in grid units of the meteorological sub-grid
            #         default is 10 (from the hysplit user manual). however,
            #         once hysplit complained and said i need to raise this
            #         variable to some value around 750...leaving w/default
            #         but change if required.
            "MGMIN": 10,

            # Maximum length of a trajectory in hours
            "KHMAX": 72,

            # Number of hours between emission start cycles
            "QCYCLE": 1.0,

            # NINIT: Read a particle initialization input file?
            # 0 - horizontal & vertical particle
            # 1 - horizontal gaussian puff, vertical top hat puff
            # 2 - horizontal & vertical top hat puff
            # 3 - horizontal gaussian puff, verticle particle
            # 4 - horizontal top hat puff, verticle particle
            "INITD": 0,

            # used to calculate the time step integration interval
            "TRATIO": 0.750,
            "DELT": 0.0,

            # particle release limits. if 0 is provided then the values are calculated
            # based on the number of sources: numpar" = num_sources" = num_fires*num_heights)
            # and maxpar" = numpar*1000/ncpus
            "NUMPAR": 1000,
            "MAXPAR": 10000000,

            ## ADVANCED Turbulence-Dispersion Computation
            ## see https://www.ready.noaa.gov/hysplitusersguide/S625.htm
            ## for more details about possible options

            # Vertical Turbulence
            "KBLT": 2,

            # Horizontal Turbulence
            "KDEF": 0,

            # Boundary Layer Stability
            "KBLS": 1,

            # Vertical Mixing Profile
            # 0 - NONE Vertical diffusivity in PBL varies w/height (DEFAULT)
            # 1 - vertical diffusivity in PBL single average value
            # 2 - scale boundary-layer values multiplied by TVMIX
            # 3 - scall free-troposphere values multiplied by TVMIX
            "KZMIX": 0,
            "TVMIX": 1.0,

            # Mixed Layer Depth Computation
            # KMIXD controls how the boundary layer depth is computed
            # 0 = Use met model MIXD if avaialable (DEFAULT)
            # 1 = Copmute from temp profile
            # 2 = Compute from TKE profile
            # 3 = Compute from modified Richardson number (STILT mode default)
            #     (new in hysplit v5.0.0)
            # >= 10 - use this value as a constant
            "KMIXD": 0,
            
            # minimum mixing depth -  default in the manual is listed as 150 m,
            # however, the code and a forum post seems to set it 250 m. also,
            # it # appears that it is different for dispersion vs trajectories.
            # so, in order to accomodate this, if hysplit.py sees a value less
            # than # zero it won't write anything to the SETUP.CFG file;
            # otherwise, it'll write the value given below
            "KMIX0": -1,

            #
            # MPI options
            #
            # This flag triggers MPI with multpile cores/processors on a single (local) node via MPICH2
            "MPI": False,

            # Number of processors/cores per HYSPLIT Process
            "NCPUS": 1,

            # Optional tranching of dispersion calculation using multiple HYSPLIT processes
            # There are two options:
            #  - Specify the number of processes (NPROCESSES) and let BlueSky determine
            #    how many fires are input into each process
            #  - Specify the number of fires per process (NFIRES_PER_PROCESS) and
            #    let BlueSky determine how many processes need to be run, up to an
            #    optional max (NPROCESSES_MAX).  The NFIRES_PER_PROCESS/NPROCESSES_MAX
            #    option is ignored if NPROCESSES is set to 1 or greater
            "NPROCESSES": 1,
            "NFIRES_PER_PROCESS": -1,
            "NPROCESSES_MAX": -1,

            # Machines file (TODO: functionality for multiple nodes)
            #MACHINEFILE": machines,

            #
            # CONTROL vars:
            #

            # sampling interval type, hour & min (default 0 1 0)
            # type of 0 gives the average over the interval
            "SAMPLING_INTERVAL_TYPE": 0,
            "SAMPLING_INTERVAL_HOUR": 1,
            "SAMPLING_INTERVAL_MIN": 0,

            # particle stuff (1.0 use default hysplit values)
            # diamater in micrometer, density in g/cc.
            "PARTICLE_DIAMETER": 1.0,
            "PARTICLE_DENSITY": 1.0,
            "PARTICLE_SHAPE": 1.0,

            # dry deposition vars (0.0 use default hysplit values)
            # velocity is m/s and weight is g/mol.
            "DRY_DEP_VELOCITY": 0.0,
            "DRY_DEP_MOL_WEIGHT": 0.0,
            "DRY_DEP_REACTIVITY": 0.0,
            "DRY_DEP_DIFFUSIVITY": 0.0,
            "DRY_DEP_EFF_HENRY": 0.0,

            # wet deposition vars (0.0 use default hysplit values)
            # in-cloud scav is L/L, below cloud is 1/s.
            "WET_DEP_ACTUAL_HENRY": 0.0,
            "WET_DEP_IN_CLOUD_SCAV": 0.0,
            "WET_DEP_BELOW_CLOUD_SCAV": 0.0,

            # radioactive decay half live in days (0.0 is default, ie: no decay)
            "RADIOACTIVE_HALF_LIVE": 0.0,

            # number of hours to offset start of dispersion
            "DISPERSION_OFFSET": 0
        },
        "vsmoke": {
            # Temperature of fire (F)
            "TEMP_FIRE": 59.0,

            # Atmospheric pressure at surface (mb)
            "PRES": 1013.25,

            # Period relative humidity
            "IRHA": 25,

            # Is fire before sunset?
            "LTOFDY": True,

            # Period instability class
            # 1 = extremely unstable
            # 2 = moderately unstable
            # 3 = slightly unstable
            # 4 = near neutral
            # 5 = slightly stable
            # 6 = moderately stable
            # 7 = extremely stable
            "STABILITY": 4,

            # Period mixing height (m)
            "MIX_HT": 1500.0,

            # Period's initial horizontal crosswind dispersion at the source (m)
            "OYINTA": 0.0,

            # Period's initial vertical dispersion at the surface (m)
            "OZINTA": 0.0,

            # Period's background PM (ug/m^3)
            "BKGPMA": 0.0,

            # Period's background CO (ppm)
            "BKGCOA": 0.0,

            # Duration of convective period of fire (decimal hours)
            "THOT": 4,

            # Duration of constant emissions period (decimal hours)
            "TCONST": 4,

            # Exponential decay constant for smoke emissions (decimal hours)
            "TDECAY": 2,

            # Emission factor for PM2.5 (lbs/ton)
            "EFPM": 30,

            # Emission factor for CO (lbs/ton)
            "EFCO": 250,

            # Period's cloud cover (tenths)
            "ICOVER": 0,

            # Period's cloud ceiling height (feet)
            "CEIL": 99999,

            # Critical contrast ratio for crossplume visibility estimates
            "CC0CRT": 0.02,

            # Visibility criterion for roadway safety
            "VISCRT": 0.125,

            #
            # RUN SETTINGS
            #

            # Plume rise: TRUE = gradual to final ht, FALSE = immediately attain final ht,
            "GRAD_RISE": True,

            # Proportion of emissions subject to plume rise
            "RFRC": -0.75,

            # Proportion of emissions subject to plume rise for each period
            "EMTQR": -0.75,

            #
            # OUTPUT SETTINGS
            #

            # KMZ Output settings
            "KMZ_FILE": "smoke_dispersion.kmz",
            "OVERLAY_TITLE": "Peak Hourly PM2.5",
            "LEGEND_IMAGE": os.path.join(_VSMOKE_IMAGES_PATH, "aqi_legend.png"),

            # GeoJSON Output settings
            "JSON_FILE": "smoke_dispersion.json",
            "CREATE_JSON": True,

            # UTM displacement of fire east of reference point
            "DUTMFE": 0,

            # UTM displacement of fire north of reference point
            "DUTMFN": 100,

            # What downward distance to start calculations (km)
            "XBGN": 150,

            # What downward distance to end calculation (km) - 200km max
            "XEND": 200,

            # Downward distance interval (km) - 0 results in default 31 distances
            "XNTVL": 0.05,

            # Tolerance for isopleths
            "TOL": 0.1
        }
    },
    "visualization": {
        "targets": [],
        "trajectories": {
            "hysplit": {
                "kml_file_name": "hysplit-trajectories.kml"
            }
        },
        "dispersion": {
            "hysplit": {
                "websky_version": "2",
                "fire_locations_csv_filename": 'fire_locations.csv',
                "fire_events_csv_filename": 'fire_events.csv',
                "smoke_dispersion_kmz_filename": 'smoke_dispersion.kmz',
                "fire_kmz_filename": 'fire_locations.kmz',
                "prettykml": False,
                "output_dir": None,
                "images_dir": None,
                "data_dir": "",
                "create_summary_json": False,
                "blueskykml_config": {
                    'SmokeDispersionKMLInput': {
                        # Use google's fire icon instead of BlueSkyKml's built-in icon
                        # (if an alternative isn't already specified)
                        # TODO: should we be using google's icon as the default?
                        'FIRE_EVENT_ICON': "http://maps.google.com/mapfiles/ms/micons/firedept.png"
                    },
                    'DispersionGridOutput': {
                        # If not set by user, it will be set to
                        # output_dir/images_dir
                        'OUTPUT_DIR': None
                    }
                },

                # The following default is defined in the blueskykml package,
                # but we need to define it here so that the code doesn't fail
                "layers": [0]
            }
        }
    },
    "export": {
        "modes": [],
        "extra_exports": [],
        "email": {
            # handle_existing needs to be defined here for exporter
            # code not to fail, even though it's not relevant to email
            "handle_existing": "fail",
            "recipients": None,
            # TODO: should there indeed be a default sender?
            "sender": "bsp@airfire.org",
            "subject": "bluesky run output",
            "smtp_server": "localhost",
            "smtp_port": 25,
            "smtp_starttls": False,
            "username": None,
            "password": None
        },
        "localsave": {
            "handle_existing": "fail",
            "output_dir_name": None,
            "extra_exports_dir_name": None,
            "json_output_filename": "output.json",
            "dest_dir": None
        },
        "upload": {
            "handle_existing": "fail",
            "output_dir_name": None,
            "extra_exports_dir_name": None,
            "json_output_filename": "output.json",

            "tarball_name": None,

            "scp_defaults": {
                "port": 22
                # TODO: did 'user' default to 'bluesky' before?
            }
            # 'scp' can be either a dict or a list of dicts of the following
            #  form
            # "scp": {
            #     "host": None,
            #     "user": None,
            #     "port": 22,
            #     "dest_dir": None
            # }
        },
        "s3": {
            "handle_existing": "replace", # Not actually used
            "output_dir_name": None,
            "extra_exports_dir_name": None,
            "json_output_filename": "output.json.gz",
            "tarball_name": None,
            "include_tarball": True,
            "bucket": None,
            "key_prefix": None,
            "default_region_name": "us-west-2",
            "compress": True
        }
    },
    "archive": {
        'tarzip': []
    }
}

PRESERVE_CASE_IN_VALUE = ['blueskykml_config']

def to_lowercase_keys(val):
    if isinstance(val, dict):
        if len(set(val.keys())) != len(set([k.lower() for k in val])):
            raise ValueError("Conflicting keys in config dict: %s",
                list(val.keys()))

        return {
            k.lower(): (to_lowercase_keys(v)
                if k.lower() not in PRESERVE_CASE_IN_VALUE
                else v)
                for k, v in val.items()
        }

    elif isinstance(val, list):
        return [to_lowercase_keys(v) for v in val]

    return copy.deepcopy(val)

DEFAULTS = to_lowercase_keys(_DEFAULTS)
