TOP_LEVEL = {
    "skip_failed_fires": False,
    "skip_failed_sources": False,
    "statuslogging": {
        #  - ***'config' > 'statuslogging' > 'enabled'*** - on/off switch
        #  - ***'config' > 'statuslogging' > 'api_endpoint'*** - i.e. http://HOSTNAME/status-logs/",
        #  - ***'config' > 'statuslogging' > 'api_key'*** - api key
        #  - ***'config' > 'statuslogging' > 'api_secret'*** - api secret
        #  - ***'config' > 'statuslogging' > 'process'*** - how you want to identify the process to the status logger
        #  - ***'config' > 'statuslogging' > 'domain'*** - how you want to identify the met domain to the status logger
    }
}


MODULE_LEVEL = {
    "load": {
        "sources": []
        # Each source has some subset of the following defined, but
        # there are no defaults to be defined here
        #  'name'
        #  'format'
        #  'type'
        #  'date_time'
        #  'file'*** -- *required* for each file type source-- file containing fire data; e.g. '/path/to/fires.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)
        #  'events_file'*** -- *optional* for each file type source-- file containing fire events data; e.g. '/path/to/fire_events.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)
        #  "wait": None, #{"strategy": None,"time": None,"max_attempts": None}
    },
    "ingestion": {
        "keep_emissions": False,
        "keep_heat": False
    },
    "merge": {
        "skip_failures": False
    },
    "filter": {
        "skip_failures": False

        #  - ***'config' > 'filter' > 'skip_failures'*** -- *optional* -- if fires filter fails, move on; default: false
        #  - ***'config' > 'filter' > 'country' > 'whitelist'*** -- *required* if 'country' section is defined and 'blacklist' array isn't -- whitelist of countries to include
        #  - ***'config' > 'filter' > 'country' > 'blacklist'*** -- *required* if 'country' section is defined and 'whiteilst' array isn't -- blacklist of countries to exclude
        #  - ***'config' > 'filter' > 'area' > 'min'*** -- *required* if 'area' section is defined and 'max' subfield isn't -- min area threshold
        #  - ***'config' > 'filter' > 'area' > 'max'*** -- *required* if 'area' section is defined and 'min' subfield isn't -- max area threshold
        #  - ***'config' > 'filter' > 'location' > 'boundary' > 'sw' > 'lat'*** -- *required* if 'location' section is defined --
        #  - ***'config' > 'filter' > 'location' > 'boundary' > 'sw' > 'lng'*** -- *required* if 'location' section is defined --
        #  - ***'config' > 'filter' > 'location' > 'boundary' > 'ne' > 'lat'*** -- *required* if 'location' section is defined --
        #  - ***'config' > 'filter' > 'location' > 'boundary' > 'ne' > 'lng'*** -- *required* if 'location' section is defined --
    },
    "splitgrowth": {
        "record_original_growth": False
    },
    "fuelbeds": {
        # The following defaults are defined in the fccsmap package,
        # so they could be removed from here
        "fccs_version": "2",
        "is_alaska": False,
        "ignored_percent_resampling_threshold": 99.9,
        "ignored_fuelbeds": ['0', '900'],
        "no_sampling": False,

        # The following defaults are defined in the fccsmap package
        # and are based on the location of the pacakge in the file
        # system. So, let fccsmap set defaults
        # "fccs_fuelload_file": None,
        # "fccs_fuelload_param": None,
        # "fccs_fuelload_grid_resolution": None,

        # the following defaults are *not* defined in fccsmap package
        "truncation_percentage_threshold": 90.0,
        "truncation_count_threshold": ; 5
    },
    "consumption": {
        "fuel_loadings": None,
        "default_ecoregion": None,
        "ecoregion_lookup_implemenation": "ogr"
    },
    "emissions": {
        # Note that 'efs' is deprecated, and so is not listed here
        "model": "feps",
        "include_emissions_details": False,
        "species": [],
        "fuel_loadings": None
    },
    "findmetdata": {
        "met_root_dir": None,
        # We need to default time_window as None, since it will be used
        # if it is defined, even if the first and last hours are None
        "time_window": None, # {"first_hour": None,"last_hour": None}

        # We need to default wait to None, since being set to None
        # or empty dict in the config indicates that we don't want
        # to wait (which is the default behavior)
        "wait": None, # {"strategy": None,"time": None,"max_attempts": None},

        "met_format": "arl",
        "arl": {
            # The following two defaults are dfined in the met package
            # TODO: should we comment them out here and leave "arl"
            #    sub-config as an empty dict
            "index_filename_pattern": "arl12hrindex.csv",
            "max_days_out": 4
        }
    },
    "localmet": {
        # The following default is defined in the met package,
        # so we won't define it here
        # "time_step": 1
    },
    "timeprofiling": {
        "hourly_fractions": None
    },

    "plumerising": {
        "model": "feps",
        "feps": {
            "working_dir": None
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
        }
    },
    "extrafiles": {
        "sets": [],
        "dest_dir": None,
        "emissionscsv": {
            "filename": None
        }
        "firescsvs": {
            "fire_locations_filename": "fire_locations.csv",
            "fire_events_filename": "fire_events.csv"

        }
    },
    "dispersion": {
        "model": "hysplit",
        "start": None,
        "num_hours": None,
        "output_dir": None,
        "working_dir": None,
        "handle_existing": "fail",
        "hsyplit": {
            #  - ***'config' > 'dispersion' > 'hysplit' > 'skip_invalid_fires'*** -- *optional* -- skips fires lacking data necessary for hysplit; default behavior is to raise an exception that stops the bluesky run
            #  - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'spacing'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
            #  - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'domain'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed -- default: 'LatLng' (which means the spacing is in degrees)
            #  - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'sw' > 'lat'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
            #  - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'sw' > 'lng'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
            #  - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'ne' > 'lat'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
            #  - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'ne' > 'lng'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
            #  - ***'config' > 'dispersion' > 'hysplit' > 'COMPUTE_GRID'*** -- *required* to be set to true if grid is not defined in met data, in 'grid' setting, or by USER_DEFINED_GRID settings -- whether or not to compute grid
            #  - ***'config' > 'dispersion' > 'hysplit' > 'GRID_LENGTH'***
            #  - ***'config' > 'dispersion' > 'hysplit' > 'CONVERT_HYSPLIT2NETCDF'*** -- *optional* -- default: true
            #  - ***'config' > 'dispersion' > 'hysplit' > 'output_file_name'*** -- *optional* -- default: 'hysplit_conc.nc'


            #  ####### Config settings adopted from BlueSky Framework

            #  - ***'config' > 'dispersion' > 'hysplit' > 'DISPERSION_OFFSET'*** -- *optional* -- number of hours to offset start of dispersion
            #  - ***'config' > 'dispersion' > 'hysplit' > 'ASCDATA_FILE'*** -- *optional* -- default: use default file in package
            #  - ***'config' > 'dispersion' > 'hysplit' > 'CENTER_LATITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none
            #  - ***'config' > 'dispersion' > 'hysplit' > 'CENTER_LONGITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DELT'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DISPERSION_FOLDER'*** -- *optional* -- default: "./input/dispersion"
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_DIFFUSIVITY'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_EFF_HENRY'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_MOL_WEIGHT'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_REACTIVITY'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_VELOCITY'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'FIRE_INTERVALS'*** -- *optional* -- default: [0, 100, 200, 500, 1000]
            #  - ***'config' > 'dispersion' > 'hysplit' > 'HEIGHT_LATITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none
            #  - ***'config' > 'dispersion' > 'hysplit' > 'ICHEM'*** -- *optional* -- default: 0; options:
            #    - 0 -> none
            #    - 1 -> matrix
            #    - 2 -> 10% / hour
            #    - 3 -> PM10 dust storm simulation
            #    - 4 -> Set concentration grid identical to the meteorology grid (not in GUI)
            #    - 5 -> Deposition Probability method
            #    - 6 -> Puff to Particle conversion (not in GUI)
            #    - 7 -> Surface water pollutant transport
            #  - ***'config' > 'dispersion' > 'hysplit' > 'INITD'*** -- *optional* -- default: 0
            #    - 0 -> horizontal & vertical particle
            #    - 1 -> horizontal gaussian puff, vertical top hat puff
            #    - 2 -> horizontal & vertical top hat puff
            #    - 3 -> horizontal gaussian puff, verticle particle
            #    - 4 -> horizontal top hat puff, verticle particle
            #  - ***'config' > 'dispersion' > 'hysplit' > 'KHMAX'*** -- *optional* -- default: 72
            #  - ***'config' > 'dispersion' > 'hysplit' > 'LANDUSE_FILE'*** -- *optional* -- default: use default file in package
            #  - ***'config' > 'dispersion' > 'hysplit' > 'MAKE_INIT_FILE'*** -- *optional* -- default: false
            #  - ***'config' > 'dispersion' > 'hysplit' > 'MAXPAR'*** -- *optional* -- default: 10000
            #  - ***'config' > 'dispersion' > 'hysplit' > 'MAX_SPACING_LONGITUDE'*** -- *optional* -- default: 0.5
            #  - ***'config' > 'dispersion' > 'hysplit' > 'MAX_SPACING_LATITUDE'*** -- *optional* -- default: 0.5
            #  - ***'config' > 'dispersion' > 'hysplit' > 'MGMIN'*** -- *optional* -- default: 10
            #  - ***'config' > 'dispersion' > 'hysplit' > 'MPI'*** -- *optional* -- default: false
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NCPUS'*** -- *optional* -- default: 1
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NCYCL'*** -- *optional* -- default: 24
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NDUMP'*** -- *optional* -- default: 24
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NFIRES_PER_PROCESS'*** -- *optional* -- default: -1 (i.e. no tranching)
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NINIT'*** -- *optional* -- default: 0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NPROCESSES'*** -- *optional* -- default: 1 (i.e. no tranching)
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NPROCESSES_MAX'*** -- *optional* -- default: -1  (i.e. no tranching)
            #  - ***'config' > 'dispersion' > 'hysplit' > 'NUMPAR'*** -- *optional* -- default: 500
            #  - ***'config' > 'dispersion' > 'hysplit' > 'OPTIMIZE_GRID_RESOLUTION'*** -- *optional* -- default: false
            # PARTICLE_DENSITY = 1.0
            # PARTICLE_DIAMETER = 1.0
            # PARTICLE_SHAPE = 1.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'PARINIT'*** -- *optional* -- default: "./input/dispersion/PARINIT"
            #  - ***'config' > 'dispersion' > 'hysplit' > 'PARDUMP'*** -- *optional* -- default: "./input/dispersion/PARDUMP"
            #  - ***'config' > 'dispersion' > 'hysplit' > 'QCYCLE'*** -- *optional* -- default: 1.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'RADIOACTIVE_HALF_LIVE'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'ROUGLEN_FILE'*** -- *optional* -- default: use default file in package
            #  - ***'config' > 'dispersion' > 'hysplit' > 'SAMPLING_INTERVAL_HOUR'*** -- *optional* -- default: 1
            #  - ***'config' > 'dispersion' > 'hysplit' > 'SAMPLING_INTERVAL_MIN '*** -- *optional* -- default: 0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'SAMPLING_INTERVAL_TYPE'*** -- *optional* -- default: 0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'SMOLDER_HEIGHT'*** -- *optional* -- default: 10.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'SPACING_LATITUDE'*** -- *required* if either COMPUTE_GRID or USER_DEFINED_GRID is true
            #  - ***'config' > 'dispersion' > 'hysplit' > 'SPACING_LONGITUDE'*** -- *required* if either COMPUTE_GRID or USER_DEFINED_GRID is true
            #  - ***'config' > 'dispersion' > 'hysplit' > 'STOP_IF_NO_PARINIT'*** -- *optional* -- default: True
            #  - ***'config' > 'dispersion' > 'hysplit' > 'TOP_OF_MODEL_DOMAIN'*** -- *optional* -- default: 30000.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'TRATIO'*** -- *optional* -- default: 0.75
            #  - ***'config' > 'dispersion' > 'hysplit' > 'USER_DEFINED_GRID'*** -- *required* to be set to true if grid is not defined in met data or in 'grid' settings, and it's not being computed -- default: False
            #  - ***'config' > 'dispersion' > 'hysplit' > 'VERTICAL_EMISLEVELS_REDUCTION_FACTOR'*** -- *optional* -- default: 1
            #  - ***'config' > 'dispersion' > 'hysplit' > 'VERTICAL_LEVELS'*** -- *optional* -- default: [100]
            #  - ***'config' > 'dispersion' > 'hysplit' > 'VERTICAL_METHOD'*** -- *optional* -- default: "DATA"
            #  - ***'config' > 'dispersion' > 'hysplit' > 'WET_DEP_ACTUAL_HENRY'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'WET_DEP_BELOW_CLOUD_SCAV'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'WET_DEP_IN_CLOUD_SCAV'*** -- *optional* -- default: 0.0
            #  - ***'config' > 'dispersion' > 'hysplit' > 'WIDTH_LONGITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none

            # Note about the grid:  There are three ways to specify the dispersion grid.
            # If USER_DEFINED_GRID is set to true, hysplit will expect BlueSky framework's
            # user defined grid settings ('CENTER_LATITUDE', 'CENTER_LONGITUDE',
            # 'WIDTH_LONGITUDE', 'HEIGHT_LATITUDE', 'SPACING_LONGITUDE', and
            # 'SPACING_LONGITUDE').  Otherwise, it will look in 'config' > 'dispersion' >
            # 'hysplit' > 'grid' for 'boundary', 'spacing', and 'domain' fields.  If not
            # defined, it will look for 'boundary', 'spacing', and 'domain' in the top level
            # 'met' object.
        },
        "vsmoke": {
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'TEMP_FIRE' -- temperature of fire (F), default: 59.0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'PRES'*** -- *optional* -- Atmospheric pressure at surface (mb); default: 1013.25
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'IRHA'*** -- *optional* -- Period relative humidity; default: 25
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'LTOFDY'*** -- *optional* -- Is fire before sunset?; default: True
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'STABILITY'*** -- *optional* -- Period instability class - 1 -> extremely unstable; 2 -> moderately unstable; 3 -> slightly unstable; 4 -> near neutral; 5 -> slightly stable; 6 -> moderately stable; 7 -> extremely stable; default: 4
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'MIX_HT'*** -- *optional* -- Period mixing height (m); default: 1500.0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'OYINTA'*** -- *optional* -- Period's initial horizontal crosswind dispersion at the source (m); default: 0.0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'OZINTA'*** -- *optional* -- Period's initial vertical dispersion at the surface (m); default: 0.0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'BKGPMA'*** -- *optional* -- Period's background PM (ug/m3); default: 0.0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'BKGCOA'*** -- *optional* -- Period's background CO (ppm); default: 0.0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'THOT'*** -- *optional* -- Duration of convective period of fire (decimal hours); default: 4
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'TCONST'*** -- *optional* -- Duration of constant emissions period (decimal hours); default: 4
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'TDECAY'*** -- *optional* -- Exponential decay constant for smoke emissions (decimal hours); default: 2
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'EFPM'*** -- *optional* -- Emission factor for PM2.5 (lbs/ton); default: 30
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'EFCO'*** -- *optional* -- Emission factor for CO (lbs/ton); default: 250
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'ICOVER'*** -- *optional* -- Period's cloud cover (tenths); default: 0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'CEIL'*** -- *optional* -- Period's cloud ceiling height (feet); default: 99999
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'CC0CRT'*** -- *optional* -- Critical contrast ratio for crossplume visibility estimates; default: 0.02
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'VISCRT'*** -- *optional* -- Visibility criterion for roadway safety; default: 0.125
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'GRAD_RISE'*** -- *optional* -- Plume rise: TRUE -> gradual to final ht; FALSE ->mediately attain final ht; default: True
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'RFRC'*** -- *optional* -- Proportion of emissions subject to plume rise; default: -0.75
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'EMTQR'*** -- *optional* -- Proportion of emissions subject to plume rise for each period; default: -0.75
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'KMZ_FILE'*** -- *optional* -- default: "smoke_dispersion.kmz"
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'OVERLAY_TITLE'*** -- *optional* -- default: "Peak Hourly PM2.5"
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'LEGEND_IMAGE'*** -- *optional* -- absolute path nem to legend; default: "aqi_legend.png" included in bluesky package
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'JSON_FILE'*** -- *optional* -- name of file to write GeoJSON dispersion data; default: "smoke_dispersion.json"
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'CREATE_JSON'*** -- *optional* -- whether or not to create the GeoJSON file; default: True
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'DUTMFE'*** -- *optional* -- UTM displacement of fire east of reference point; default: 0
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'DUTMFN'*** -- *optional* -- UTM displacement of fire north of reference point; default: 100
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'XBGN'*** -- *optional* -- What downward distance to start calculations (km); default: 150
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'XEND'*** -- *optional* -- What downward distance to end calculation (km) - 200km max; default: 200
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'XNTVL'*** -- *optional* -- Downward distance interval (km) - 0 results in default 31 distances; default: 0.05
            #  - ***'config' > 'dispersion' > 'vsmoke' > 'TOL'*** -- *optional* -- Tolerance for isopleths; detault: 0.1
        }
    },
    "visualization": {
        "target": "'dispersion'"
        "hysplit": {
            "fire_locations_csv_filename": 'fire_locations.csv',
            "fire_events_csv_filename": 'fire_events.csv',
            "smoke_dispersion_kmz_filename": 'smoke_dispersion.kmz',
            "fire_kmz_filename": 'fire_locations.kmz',
            "prettykml": False,
            "output_dir": None,
            "images_dir": None,
            "data_dir": "",
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
            }

            # The following defaults are defined in the blueskykml package,
            # so they don't need to be defined here
            #"layers": [0],
        }
    },
    "export": {
        "modes": [],
        "extra_exports": [],
        "email": {
            # - ***'config' > 'export' > 'email' > 'recipients'*** -- *required* --
            # - ***'config' > 'export' > 'email' > 'sender'*** -- *optional* -- defaults to 'bsp@airfire.org'
            # - ***'config' > 'export' > 'email' > 'subject'*** -- *optional* -- defaults to 'bluesky run output'
            # - ***'config' > 'export' > 'email' > 'smtp_server'*** -- *optional* -- defaults to 'localhost'
            # - ***'config' > 'export' > 'email' > 'smtp_port'*** -- *optional* -- defaults to 1025
            # - ***'config' > 'export' > 'email' > 'smtp_starttls'*** -- *optional* -- defaults to False
            # - ***'config' > 'export' > 'email' > 'username'*** -- *optional* --
            # - ***'config' > 'export' > 'email' > 'password'*** -- *optional* --
        },
        "localsave": {

            #  - ***'config' > 'export' > 'localsave' > 'output_dir_name'*** -- *optional* -- defaults to run_id, which is generated if not defined
            #  - ***'config' > 'export' > 'localsave' > 'extra_exports_dir_name'*** -- *optional* -- generated from extra_exports mode name(s) if not defined
            #  - ***'config' > 'export' > 'localsave' > 'json_output_filename'*** -- *optional* -- defaults to 'output.json'
            #  - ***'config' > 'export' > 'localsave' > 'dest_dir'*** - *required* -- destination directory to contain output directory
            #  - ***'config' > 'export' > 'localsave' > 'handle_existing'*** - *optional* -- how to handle case where output dir already exists; options: 'replace', 'write_in_place', 'fail'; defaults to 'fail'
        },
        "upload": {
            #  - ***'config' > 'export' > 'upload' > 'output_dir_name'*** -- *optional* -- defaults to run_id, which is generated if not defined
            #  - ***'config' > 'export' > 'upload' > 'extra_exports_dir_name'*** -- *optional* -- generated from extra_exports mode name(s) if not defined
            #  - ***'config' > 'export' > 'upload' > 'json_output_filename'*** -- *optional* -- defaults to 'output.json'

            #  - ***'config' > 'export' > 'upload' > 'tarball_name'*** - *optional* -- defaults to '<output_dir>.tar.gz'
            #  - ***'config' > 'export' > 'upload' > 'scp' > 'host'*** - *required* if uploading via scp (which is currently the only supported upload mode) -- hostname of server to scp to
            #  - ***'config' > 'export' > 'upload' > 'scp' > 'user'*** - *optional* if uploading via scp (which is currently the only supported upload mode) -- username to use in scp; defaults to 'bluesky'
            #  - ***'config' > 'export' > 'upload' > 'scp' > 'port'*** - *optional* if uploading via scp (which is currently the only supported upload mode) -- port to use in scp; defaults to 22
            #  - ***'config' > 'export' > 'upload' > 'scp' > 'dest_dir'*** - *required* if uploading via scp (which is currently the only supported upload mode) -- destination directory on remote host to contain output directory
        }
    }

}