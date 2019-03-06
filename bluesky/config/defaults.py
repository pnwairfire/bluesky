DEFAULTS = {
    "skip_failed_fires": False,
    "skip_failed_sources"
    "load": {
        "sources": []
    }


#  - ***'config' > 'load' > 'sources'*** -- *optional* -- array of sources to load fire data from; if not defined or if empty array, nothing is loaded
#  - ***'config' > 'load' > 'sources' > 'name'*** -- *required* for each source-- e.g. 'smartfire2'
#  - ***'config' > 'load' > 'sources' > 'format'*** -- *required* for each source-- e.g. 'csv'
#  - ***'config' > 'load' > 'sources' > 'type'*** -- *required* for each source-- e.g. 'file'
#  - ***'config' > 'load' > 'sources' > 'date_time'*** -- *optional* for each source-- e.g. '20160412', '2016-04-12T12:00:00'; used to to replace any datetime formate codes in the file name; defaults to current date (local time)
#  - ***'config' > 'load' > 'sources' > 'wait' > 'strategy'*** -- *required* if 'wait' section is defined -- 'fixed' or 'backoff'
#  - ***'config' > 'load' > 'sources' > 'wait' > 'time'*** -- *required* if 'wait' section is defined -- time to wait until next attempt (initial wait only if backoff)
#  - ***'config' > 'load' > 'sources' > 'wait' > 'max_attempts'*** -- *required* if 'wait' section is defined  -- max number of attempts

#  - ***'config' > 'load' > 'sources' > 'file'*** -- *required* for each file type source-- file containing fire data; e.g. '/path/to/fires.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)
#  - ***'config' > 'load' > 'sources' > 'events_file'*** -- *optional* for each file type source-- file containing fire events data; e.g. '/path/to/fire_events.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)

#  - ***'config' > 'ingestion' > 'keep_emissions'*** -- *optional* keep any emissions, if specified, and record in growth object
#  - ***'config' > 'ingestion' > 'keep_heat'*** -- *optional* keep heat, if specified, and record in growth object

#  - ***'config' > 'merge' > 'skip_failures'*** -- *optional* -- if fires fail to merge, keep separate and move on; default: false

#  - ***'config' > 'filter' > 'skip_failures'*** -- *optional* -- if fires filter fails, move on; default: false
#  - ***'config' > 'filter' > 'country' > 'whitelist'*** -- *required* if 'country' section is defined and 'blacklist' array isn't -- whitelist of countries to include
#  - ***'config' > 'filter' > 'country' > 'blacklist'*** -- *required* if 'country' section is defined and 'whiteilst' array isn't -- blacklist of countries to exclude
#  - ***'config' > 'filter' > 'area' > 'min'*** -- *required* if 'area' section is defined and 'max' subfield isn't -- min area threshold
#  - ***'config' > 'filter' > 'area' > 'max'*** -- *required* if 'area' section is defined and 'min' subfield isn't -- max area threshold
#  - ***'config' > 'filter' > 'location' > 'boundary' > 'sw' > 'lat'*** -- *required* if 'location' section is defined --
#  - ***'config' > 'filter' > 'location' > 'boundary' > 'sw' > 'lng'*** -- *required* if 'location' section is defined --
#  - ***'config' > 'filter' > 'location' > 'boundary' > 'ne' > 'lat'*** -- *required* if 'location' section is defined --
#  - ***'config' > 'filter' > 'location' > 'boundary' > 'ne' > 'lng'*** -- *required* if 'location' section is defined --

#  - ***'config' > 'splitgrowth' > 'record_original_growth'*** -- *optional* --

#  - ***'config' > 'fuelbeds' > 'ignored_fuelbeds'*** -- *optional* -- default ['0', '900']
#  - ***'config' > 'fuelbeds' > 'truncation_percentage_threshold'*** -- *optional* -- use first N largest fuelbeds making up this percentage for a location; default 90.0
#  - ***'config' > 'fuelbeds' > 'truncation_count_threshold'*** -- *optional* -- use only up to this many fuelbeds for a location; default 5
#  - ***'config' > 'fuelbeds' > 'fccs_version'*** -- *optional* -- '1' or '2'
#  - ***'config' > 'fuelbeds' > 'fccs_fuelload_file'*** -- *optional* -- NetCDF
#    file containing FCCS lookup map
#  - ***'config' > 'fuelbeds' > 'fccs_fuelload_param'*** -- *optional* -- name of variable in NetCDF file
#  - ***'config' > 'fuelbeds' > 'fccs_fuelload_grid_resolution'*** -- *optional* -- length of grid cells in km
#  - ***'config' > 'fuelbeds' > 'ignored_fuelbeds'*** -- *optional* -- fuelbeds to ignore
#  - ***'config' > 'fuelbeds' > 'ignored_percent_resampling_threshold'*** -- *optional* -- percentage of ignored fuelbeds which should trigger resampling in larger area; only plays a part in Point and MultiPoint look-ups
#  - ***'config' > 'fuelbeds' > 'no_sampling'*** -- *optional* -- don't sample surrounding area for Point and MultiPoint geometries

#  - ***'config' > 'consumption' > 'fuel_loadings'*** -- *optional* -- custom, fuelbed-specific fuel loadings
#  - ***'config' > 'consumption' > 'default_ecoregion'*** -- *optional* -- ecoregion to use in case fire info lacks it and lookup fails; e.g. 'western', 'southern', 'boreal'

#  - ***'config' > 'emissions' > 'model'*** -- *optional* -- emissions model; 'prichard-oneill' (which replaced 'urbanski'), 'feps', or 'consume'; default 'feps'
#  - ***'config' > 'emissions' > 'efs'*** -- *optional* -- deprecated synonym for 'model'
#  - ***'config' > 'emissions' > 'species'*** -- *optional* -- whitelist of species to compute emissions levels for
#  - ***'config' > 'emissions' > 'include_emissions_details'*** -- *optional* -- whether or not to include emissions levels by fuel category; default: false

# - ***'config' > 'emissions' > 'fuel_loadings'*** -- *optional* -- custom, fuelbed-specific fuel loadings, used for piles; Note that the code looks in
# 'config' > 'consumption' > 'fuel_loadings' if it doesn't find them in the
# emissions config

#  - ***'config' > 'findmetdata' > 'met_root_dir'*** -- *required* --
#  - ***'config' > 'findmetdata' > 'time_window' > 'first_hour'*** -- *required* if fire growth data isn't defined --
#  - ***'config' > 'findmetdata' > 'time_window' > 'last_hour'*** -- *required* if fire growth data isn't defined --
#  - ***'config' > 'findmetdata' > 'met_format'*** -- *optional* -- defaults to 'arl'
#  - ***'config' > 'findmetdata' > 'wait' > 'strategy'*** -- *required* if 'wait' section is defined -- 'fixed' or 'backoff'
#  - ***'config' > 'findmetdata' > 'wait' > 'time'*** -- *required* if 'wait' section is defined -- time to wait until next attempt (initial wait only if backoff)
#  - ***'config' > 'findmetdata' > 'wait' > 'max_attempts'*** -- *required* if 'wait' section is defined  -- max number of attempts
#  - ***'config' > 'findmetdata' > 'arl' > 'index_filename_pattern'*** -- *optional* -- defaults to 'arl12hrindex.csv'
#  - ***'config' > 'findmetdata' > 'arl' > 'max_days_out'*** -- *optional* -- defaults to 4

# - ***'config' > 'localmet' > 'time_step'*** -- *optional* -- hour per arl file time step; defaults to 1

#  - ***'config' > 'timeprofiling' > 'hourly_fractions'*** -- *optional* -- custom hourly fractions (either 24-hour fractions or for the span of the growth window)


#  - ***'config' > 'plumerising' > 'model'*** -- *optional* -- plumerise model; defaults to "feps"

#  - ***'config' > 'plumerising' > 'feps' > 'feps_weather_binary'*** -- *optional* -- defaults to "feps_weather"
#  - ***'config' > 'plumerising' > 'feps' > 'feps_plumerise_binary'*** -- *optional* -- defaults to "feps_plumerise"
#  - ***'config' > 'plumerising' > 'feps' > 'plume_top_behavior'*** -- *optional* -- how to model plume top; options: 'Briggs', 'FEPS', 'auto'; defaults to 'auto'
#  - ***'config' > 'plumerising' > 'feps' > 'working_dir'*** -- *optional* -- where to write intermediate files; defaults to writing to tmp dir

#  - ***'config' > 'plumerising' > 'sev' > 'alpha'*** -- *optional* -- default: 0.24
#  - ***'config' > 'plumerising' > 'sev' > 'beta'*** -- *optional* -- default: 170
#  - ***'config' > 'plumerising' > 'sev' > 'ref_power'*** -- *optional* -- default: 1e6
#  - ***'config' > 'plumerising' > 'sev' > 'gamma'*** -- *optional* -- default: 0.35
#  - ***'config' > 'plumerising' > 'sev' > 'delta'*** -- *optional* -- default: 0.6
#  - ***'config' > 'plumerising' > 'sev' > 'ref_n'*** -- *optional* -- default: 2.5e-4
#  - ***'config' > 'plumerising' > 'sev' > 'gravity'*** -- *optional* -- default: 9.8
#  - ***'config' > 'plumerising' > 'sev' > 'plume_bottom_over_top'*** -- *optional* -- default: 0.5


# - ***'config' > 'extrafiles' > 'dest_dir' -- *required* -- where to write extra files
# - ***'config' > 'extrafiles' > 'sets' -- *optional* (though nothing happens if not defined) -- array of file sets to write

# - ***'config' > 'extrafiles' > 'emissionscsv' > 'filename'*** -- *required* --

# - ***'config' > 'extrafiles' > 'firescsvs' > 'fire_locations_filename'*** -- *optional* -- default: 'fire_locations.csv'
# - ***'config' > 'extrafiles' > 'firescsvs' > 'fire_events_filename'*** -- *optiona* -- default: 'fire_events.csv'


#  - ***'config' > 'dispersion' > 'start'*** -- *required* (unless it can be determined from fire growth windows) -- modeling start time (ex. "2015-01-21T00:00:00Z"); 'today' is also recognized, in which case start is set to midnight of the current utc date
#  - ***'config' > 'dispersion' > 'num_hours'*** -- *required* (unless it can be determined from fire growth windows) -- number of hours in model run
#  - ***'config' > 'dispersion' > 'output_dir'*** -- *required* -- directory to contain output
#  - ***'config' > 'dispersion' > 'model'*** -- *optional* -- dispersion model; defaults to "hysplit"
#  - ***'config' > 'dispersion' > 'handle_existing'*** - *optional* -- how to handle case where output dir already exists; options: 'replace', 'write_in_place', 'fail'; defaults to 'fail'

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

#  - ***'config' > 'visualization' > 'target'*** -- *optional* -- defaults to dispersion

#  - ***'config' > 'visualization' > 'hysplit' > 'smoke_dispersion_kmz_filename'*** -- *optional* -- defaults to 'smoke_dispersion.kmz'
#  - ***'config' > 'visualization' > 'hysplit' > 'fire_kmz_filename'*** -- *optional* -- defaults to 'smoke_dispersion.kmz'
#  - ***'config' > 'visualization' > 'hysplit' > 'fire_locations_csv_filename'*** -- *optional* -- defaults to 'fire_locations.csv'
#  - ***'config' > 'visualization' > 'hysplit' > 'fire_events_csv_filename'*** -- *optional* -- defaults to 'fire_events.csv'
#  - ***'config' > 'visualization' > 'hysplit' > 'layers'*** -- *optional* -- defaults to [0]
#  - ***'config' > 'visualization' >  'hysplit' > 'prettykml'*** -- *optional* -- whether or not to make the kml human readable; defaults to false
#  - ***'config' > 'visualization' >  'hysplit' > 'output_dir' -- *optional* -- where to create visualization output; if not specified, visualization output will go in hysplit output directory
#  - ***'config' > 'visualization' >  'hysplit' > 'images_dir' -- *optional* -- sub-directory to contain images (relative to output direcotry); default is 'graphics/''
#  - ***'config' > 'visualization' >  'hysplit' > 'data_dir' -- *optional* -- sub-directory to contain data files (relative to output direcotry); default is output directory root
#  - ***'config' > 'visualization' >  'hysplit' > 'blueskykml_config' -- *optional* -- contains configuration to pass directly into blueskykml; expected to be nested with top level section keys and second level option keys; see https://github.com/pnwairfire/blueskykml/ for configuration options

# - ***'config' > 'export' > 'modes' -- *optional* -- defaults to 'email'
# - ***'config' > 'export' > 'extra_exports' -- *optional* -- array of extra output files to export (ex. 'dispersion' or 'visualization' outputs); defaults to none

# - ***'config' > 'export' > 'email' > 'recipients'*** -- *required* --
# - ***'config' > 'export' > 'email' > 'sender'*** -- *optional* -- defaults to 'bsp@airfire.org'
# - ***'config' > 'export' > 'email' > 'subject'*** -- *optional* -- defaults to 'bluesky run output'
# - ***'config' > 'export' > 'email' > 'smtp_server'*** -- *optional* -- defaults to 'localhost'
# - ***'config' > 'export' > 'email' > 'smtp_port'*** -- *optional* -- defaults to 1025
# - ***'config' > 'export' > 'email' > 'smtp_starttls'*** -- *optional* -- defaults to False
# - ***'config' > 'export' > 'email' > 'username'*** -- *optional* --
# - ***'config' > 'export' > 'email' > 'password'*** -- *optional* --

#  - ***'config' > 'export' > ['localsave'|'upload'] > 'output_dir_name'*** -- *optional* -- defaults to run_id, which is generated if not defined
#  - ***'config' > 'export' > ['localsave'|'upload'] > 'extra_exports_dir_name'*** -- *optional* -- generated from extra_exports mode name(s) if not defined
#  - ***'config' > 'export' > ['localsave'|'upload'] > 'json_output_filename'*** -- *optional* -- defaults to 'output.json'

#  - ***'config' > 'export' > 'localsave' > 'dest_dir'*** - *required* -- destination directory to contain output directory
#  - ***'config' > 'export' > 'localsave' > 'handle_existing'*** - *optional* -- how to handle case where output dir already exists; options: 'replace', 'write_in_place', 'fail'; defaults to 'fail'

#  - ***'config' > 'export' > 'upload' > 'tarball_name'*** - *optional* -- defaults to '<output_dir>.tar.gz'
#  - ***'config' > 'export' > 'upload' > 'scp' > 'host'*** - *required* if uploading via scp (which is currently the only supported upload mode) -- hostname of server to scp to
#  - ***'config' > 'export' > 'upload' > 'scp' > 'user'*** - *optional* if uploading via scp (which is currently the only supported upload mode) -- username to use in scp; defaults to 'bluesky'
#  - ***'config' > 'export' > 'upload' > 'scp' > 'port'*** - *optional* if uploading via scp (which is currently the only supported upload mode) -- port to use in scp; defaults to 22
#  - ***'config' > 'export' > 'upload' > 'scp' > 'dest_dir'*** - *required* if uploading via scp (which is currently the only supported upload mode) -- destination directory on remote host to contain output directory

#  - ***'config' > 'statuslogging' > 'enabled'*** - on/off switch
#  - ***'config' > 'statuslogging' > 'api_endpoint'*** - i.e. http://HOSTNAME/status-logs/",
#  - ***'config' > 'statuslogging' > 'api_key'*** - api key
#  - ***'config' > 'statuslogging' > 'api_secret'*** - api secret
#  - ***'config' > 'statuslogging' > 'process'*** - how you want to identify the process to the status logger
#  - ***'config' > 'statuslogging' > 'domain'*** - how you want to identify the met domain to the status logger


}