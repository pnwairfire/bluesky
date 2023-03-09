# Configuring BlueSky Runs

Config settings can be specified in separate config file(s) as well
as via command line options.  Config files are loaded in the
order they appear on the command line, with each subsequent files
overriding any config parameters already set. Next, the comand line
settings are applied in the order they are specified, overriding
any config paramters already set.

For example if config1.json specifies foo=bar and bar=1, and
config2.json specifies foo=baz and baz=3, and if bsp is invoked like:

    $ bsp -i input.json -c config1.json -c config2.json

then the net result is foo=baz, bar=1, baz=3.  If you add
'-C foo=bsdf' to the command

    $ bsp -i input.json -c config1.json -c config2.json -C foo=bsdf

then regardless of where it is specified in the command, foo
will be 'bsdf', bar will remain 1, and baz will remain 3.

The command line options are specifying configuration are:

  - `-C`, `--config-option`
  - `-B`, `--boolean-config-option`
  - `-I`, `--integer-config-option`
  - `-F`, `--float-config-option`
  - `-J`, `--json-config-option`
  - `-c`, `--config-file`

Use `bsp`'s `-h` option to get more more information about each
config related option.

## 'config' Fields

The 'config' object has sub-objects specific to the modules to be run, as
well as top level fields that apply to multiple modules. As with
the fire data, each module has its own set of required and optional fields.

***Note that, with the exception of keys under
visualization > hysplit > blueskykml, all keys in the
configuration json data are case-insensitive.***

### Top Level Fields

 - ***'config' > 'skip_failed_fires'*** -- *optional* -- exclude failed fire rather than abort entire run; default false; applies to various modules
 - ***'config' > 'skip_failed_sources'*** -- *optional* -- exclude failed sources rather than abort entire run; default false;  *Note: this may alternatively be defined under 'load'*

### input

 - ***'config' > 'input' > 'input_file_failure_tolerance'*** -- Level of tolerance for input file failures - 'none', 'partial', 'complete'; default 'partial'
   - 'none': abort execution if any input files fail to load
   - 'partial': abort execution only if all input files fail to load
   - 'complete': Never abort execution on input failures
 - ***'config' > 'input' > 'wait' > 'strategy'*** -- *required* if 'wait' section is defined -- 'fixed' or 'backoff'
 - ***'config' > 'input' > 'wait' > 'time'*** -- *required* if 'wait' section is defined -- time to wait until next attempt (initial wait only if backoff)
 - ***'config' > 'input' > 'wait' > 'max_attempts'*** -- *required* if 'wait' section is defined  -- max number of attempts


### load

 - ***'config' > 'load' > 'sources'*** -- *optional* -- array of sources to load fire data from; if not defined or if empty array, nothing is loaded
 - ***'config' > 'load' > 'sources' > 'name'*** -- *required* for each source-- e.g. 'firespider'
 - ***'config' > 'load' > 'sources' > 'format'*** -- *required* for each source-- e.g. 'csv'
 - ***'config' > 'load' > 'sources' > 'type'*** -- *required* for each source-- e.g. 'file'
 - ***'config' > 'load' > 'sources' > 'wait' > 'strategy'*** -- *required* if 'wait' section is defined -- 'fixed' or 'backoff'
 - ***'config' > 'load' > 'sources' > 'wait' > 'time'*** -- *required* if 'wait' section is defined -- time to wait until next attempt (initial wait only if backoff)
 - ***'config' > 'load' > 'sources' > 'wait' > 'max_attempts'*** -- *required* if 'wait' section is defined  -- max number of attempts
 - ***'config' > 'load' > 'sources' > 'saved_copy_file'*** -- *optional* - save copy of loaded fire data to file
 - ***'config' > 'load' > 'sources' > 'saved_copy_events_file'*** -- *optional* - save copy of loaded fire events data to file
 - ***'config' > 'load' > 'sources' > 'start'*** -- used to filter fires based on time
 - ***'config' > 'load' > 'sources' > 'end'*** -- used to filter fires based on time
 - ***'config' > 'load' > 'sources' > 'skip_failures'*** -- skip fires that result in exception during load

#### if source 'bsf'

 - ***'config' > 'load' > 'sources' > 'omit_nulls'*** -- don't include fire data keys with null/None values
 - ***'config' > 'load' > 'sources' > 'timeprofile_file'*** -- *optional*
 - ***'config' > 'load' > 'sources' > 'load_consumption'*** -- *optional*
 - ***'config' > 'load' > 'sources' > 'load_emissions'*** -- *optional*

#### if type 'file':

 - ***'config' > 'load' > 'sources' > 'file'*** -- *required* for each file type source-- file containing fire data; e.g. '/path/to/fires.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.); note that csv files can be loaded over http(s)
 - ***'config' > 'load' > 'sources' > 'events_file'*** -- *optional* for each file type source-- file containing fire events data; e.g. '/path/to/fire_events.csv'; may contain format codes that conform to the C standard (e.g. '%Y' for four digit year, '%m' for zero-padded month, etc.)

#### if type 'API':

 - ***'config' > 'load' > 'sources' > 'endpoint'*** --
 - ***'config' > 'load' > 'sources' > 'key'*** --
 - ***'config' > 'load' > 'sources' > 'secret'*** --
 - ***'config' > 'load' > 'sources' > 'key_param'*** --
 - ***'config' > 'load' > 'sources' > 'auth_protocol'*** --
 - ***'config' > 'load' > 'sources' > 'request_timeout'*** --
 - ***'config' > 'load' > 'sources' > 'query'*** --

### merge

 - ***'config' > 'merge' > 'skip_failures'*** -- *optional* -- if fires fail to merge, keep separate and move on; default: false

### filter

 - ***'config' > 'filter' > 'skip_failures'*** -- *optional* -- if fires filter fails, move on; default: false
 - ***'config' > 'filter' > 'area' > 'min'*** -- *required* if 'area' section is defined and 'max' subfield isn't -- min area threshold
 - ***'config' > 'filter' > 'area' > 'max'*** -- *required* if 'area' section is defined and 'min' subfield isn't -- max area threshold
 - ***'config' > 'filter' > 'location' > 'boundary' > 'sw' > 'lat'*** -- *required* if 'location' section is defined --
 - ***'config' > 'filter' > 'location' > 'boundary' > 'sw' > 'lng'*** -- *required* if 'location' section is defined --
 - ***'config' > 'filter' > 'location' > 'boundary' > 'ne' > 'lat'*** -- *required* if 'location' section is defined --
 - ***'config' > 'filter' > 'location' > 'boundary' > 'ne' > 'lng'*** -- *required* if 'location' section is defined --
  - ***'config' > 'filter' > 'time' > 'start'*** -- *required* if 'time' section is defined and 'end' isn't specified -- 'start' and 'end' may be specified together; note that the specified time is assumed to be UTC unless it ends with 'L', in which case it is compared against the activity 'end' times unadjusted for utc offset
  - ***'config' > 'filter' > 'time' > 'end'*** --  *required* if 'time' section is defined and 'start' isn't specified -- 'start' and 'end' may be specified together; note that the specified time is assumed to be UTC unless it ends with 'L', in which case it is compared against the activity 'start' times unadjusted for utc offset

The following settings apply to filtering on any field (other than 'area') in the active_area or location ('specified_points' or 'perimeter') objects:

 - ***'config' > 'filter' > 'ANY_FIELD' > 'include'*** -- *required* if 'exclude' array isn't defined -- list of values to include
 - ***'config' > 'filter' > 'ANY_FIELD' > 'exclude'*** -- *required* if 'include' array isn't defined -- list of values to exclude
 - ***'config' > 'filter' > 'ANY_FIELD' > 'scope'*** -- *optional* -- options: 'active_area', 'location'; default: 'active_area'; where to look for field in bluesky data structure
 - ***'config' > 'filter' > 'ANY_FIELD' > 'tolerance'*** -- *optional* -- options: 'any', 'all'; default: 'any'; whether to look for any matches or all

### fuelbeds

- ***'config' > 'fuelbeds' > 'fccs_version'*** -- *optional* -- '1' or '2'
- ***'config' > 'fuelbeds' > 'ignored_percent_resampling_threshold'*** -- *optional* -- percentage of ignored fuelbeds which should trigger resampling in larger area; only plays a part in Point and MultiPoint look-ups
- ***'config' > 'fuelbeds' > 'ignored_fuelbeds'*** -- *optional* -- fuelbeds to ignore; default ['0', '900']
- ***'config' > 'fuelbeds' > 'no_sampling'*** -- *optional* -- don't sample surrounding area for Point and MultiPoint geometries
- ***'config' > 'fuelbeds' > 'use_all_grid_cells'*** -- *optional* --
- ***'config' > 'fuelbeds' > 'sampling_radius_factors'*** -- *optional* --
- ***'config' > 'fuelbeds' > 'skip_failures'*** -- *optional* -- default `false`; if true, ignore fuelbed look-up failures and move on to next location; else (default), raise exception (which either aborts run or moves fire to `failed_fires`, depending on how top level `skip_failed_fires` is set)
- ***'config' > 'fuelbeds' > 'fccs_fuelload_file'*** -- *optional* -- NetCDF
  file containing FCCS lookup map
- ***'config' > 'fuelbeds' > 'fccs_fuelload_param'*** -- *optional* -- name of variable in NetCDF file
- ***'config' > 'fuelbeds' > 'fccs_fuelload_grid_resolution'*** -- *optional* -- length of grid cells in km
- ***'config' > 'fuelbeds' > 'truncation_percentage_threshold'*** -- *optional* -- use first N largest fuelbeds making up this percentage for a location; default 90.0
- ***'config' > 'fuelbeds' > 'truncation_count_threshold'*** -- *optional* -- use only up to this many fuelbeds for a location; default 5
- ***'config' > 'fuelbeds' > 'total_pct_threshold'*** -- *optional* -- Allow summed fuel percentages to be this much off of 100%; default is 0.5% (i.e. between 99.5% and 100.5%)

### ecoregion

 - ***'config' > 'ecoregion' > 'lookup_implementation'*** -- *optional* -- default 'ogr'
 - ***'config' > 'ecoregion' > 'skip_failures'*** -- *optional* -- default true; if true (default) continue on to next location in fire; else, raise exception
 - ***'config' > 'ecoregion' > 'default'*** -- *optional* -- ecoregion to use in case fire info lacks it and lookup fails; e.g. 'western', 'southern', 'boreal'

### fuelmoisture

 - ***'config' > 'fuelmoisture' > 'models'*** -- *optional* -- fuel moisture models to run; default ["nfdrs"]
 - ***'config' > 'fuelmoisture' > 'use_defaults'*** -- *optional* -- after running fuel moisture models, set any remaining undefined fields to defaults, based on fire type (wildfire vs rx); otherwise, the fields are left undefined and other modules dependent on fuel moisture will use their own defaults
 - ***'config' > 'fuelmoisture' > 'defaults_profile'*** -- *optional* -- if using defaults, 'defaults_profile' indicates which one of the defined profiles ("very_dry', 'dry', 'moderate', 'moist', 'wet', 'very_wet'). If not set (default behavior), bluesky uses 'dry' for wildfires and 'moist' for everything else
 - ***'config' > 'fuelmoisture' > 'skip_failures'*** -- *optional* -- default `true`; if true (default) ignore and move on to next model or location; else, raise exception (which either aborts run or moves fire to `failed_fires`, depending on how top level `skip_failed_fires` is set)
#### if running NFDRS

***(There aren't currently any config parameters for the NFDRS model)***

#### if running WIMS

 - ***'config' > 'fuelmoisture' > 'wims' > 'url' *** -- *optional* -- source of wims data to download; default: https://www.wfas.net/archive/www.fs.fed.us/land/wfas/archive/%Y/%m/%d/fdr_obs.dat  ***(Note that this source stopped publishing new data in May 2019)***
 - ***'config' > 'fuelmoisture' > 'wims' > 'data_dir' *** -- *optional* -- where to write downloaded data; defaults to tmp directory

### consumption

 - ***'config' > 'consumption' > 'fuel_loadings'*** -- *optional* -- custom, fuelbed-specific fuel loadings

The following consume_settings fields define what defaults to use when the
field isn't defined in a fire's activity object (or in its localmet data, if
it's a met related field).
They also define what synonyms to recognize, if any, for each field.

 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'slope' > 'default'*** -- *optional* -- percent, from 1 to 100; default 5
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'windspeed' > 'default'*** -- *optional* -- default 6; valid values: 0 to 35
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'days_since_rain' > 'default'*** -- *optional* -- default 10,   # our default
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'days_since_rain' > 'synonyms'*** -- *optional* -- default ['rain_days']
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'fuel_moisture_10hr_pct' > 'default'*** -- *optional* -- default 50
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'fuel_moisture_10hr_pct' > 'synonyms'*** -- *optional* -- default ['moisture_10hr']
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'length_of_ignition' > 'default'*** -- *optional* -- in minutes; default 120; used if `ignition_start` and `ignition_end` aren't specified for a fire
 - ***'config' > 'consumption' > 'consume_settings' > 'activity' > 'fm_type' > 'default'*** -- *optional* -- defailt "MEAS-Th"
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'fuel_moisture_1000hr_pct' > 'default'*** -- *optional* -- default 30
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'fuel_moisture_1000hr_pct' > 'synonyms'*** -- *optional* -- default ['moisture_1khr']
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'fuel_moisture_duff_pct' > 'default'*** -- *optional* -- default 75
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'fuel_moisture_duff_pct' > 'synonyms'*** -- *optional* -- default ['moisture_duff']
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'fuel_moisture_litter_pct' > 'default'*** -- *optional* -- default 16
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'fuel_moisture_litter_pct' > 'synonyms'*** -- *optional* -- default ['moisture_litter']
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'canopy_consumption_pct' > 'default'*** -- *optional* -- default 0
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'shrub_blackened_pct' > 'default'*** -- *optional* -- default 50
 - ***'config' > 'consumption' > 'consume_settings' > 'all' > 'pile_blackened_pct' > 'default'*** -- *optional* -- default 0

### emissions

 - ***'config' > 'emissions' > 'model'*** -- *optional* -- emissions model; 'prichard-oneill' (which replaced 'urbanski'), 'feps', or 'consume'; default 'feps'
 - ***'config' > 'emissions' > 'species'*** -- *optional* -- list of species to compute emissions levels for
 - ***'config' > 'emissions' > 'include_emissions_details'*** -- *optional* -- whether or not to include emissions levels by fuel category; default: false
 - ***'config' > 'emissions' > 'include_emissions_factors'*** -- *optional* -- whether or not to include the emissions factors used for computing emissions in the output data; default: false

#### If running consume emissions:

- ***'config' > 'emissions' > 'fuel_loadings'*** -- *optional* -- custom, fuelbed-specific fuel loadings, used for piles; Note that the code looks in
'config' > 'consumption' > 'fuel_loadings' if it doesn't find them in the
emissions config

#### If running ubc-bsf-feps emissions:

- ***'config' > 'emissions' > 'ubc-bsf-feps' > 'working_dir'*** -- *optional* --
- ***'config' > 'emissions' > 'ubc-bsf-feps' > 'delete_working_dir_if_no_error'*** -- *optional* -- default true

### growth

 - ***'config' > 'growth' > 'model'*** -- *optional* -- growth model; currently, only 'persistence' is supported; default: 'persistence'

#### If running persistence:

'config' > 'growth' > 'persistence' may point to a single object or
an array of objects.  If an array, the first matching object will be used
for the date to persist.
For example, consider a persistence configuration where the first
set of params specify 1 day at 50% from January 1st through May 31st, the
second set specify 3 days at 100% from June 1st through September 30th, and
the third set specify one day at 50% from October 1st through Dec 31st. If
'today' is November 1st, and it's the date to persist, then the third set of
parameters would be used.

 - ***'config' > 'growth' > 'persistence' > 'date_to_persist'*** -- *optional* -- default: whatever 'today' is set to; note that active area dates, which are local, are compared to this date as is
 - ***'config' > 'growth' > 'persistence' > 'days_to_persist'*** -- *optional* -- default: 1; can't be specified if 'daily_percentages' is also specified
 - ***'config' > 'growth' > 'persistence' > 'daily_percentages'*** -- *optional* -- default: [100]; can't be specified if 'days_to_persist' is also specified
 - ***'config' > 'growth' > 'persistence' > 'truncate'*** -- *optional* -- If there is activity after the date to persist, and if 'truncate' is set to true, all activity after the date to persist is deleted and replaced with persisted activity, otherwise it is left in place and the persistence module moves on to the next active area; default: false
 - ***'config' > 'growth' > 'persistence' > 'start_day'*** -- *optional* -- Formatted as '%m-%d' (e.g. '06-01'), '%b %d' (e.g. 'Jun 01'), '%B %d' (e.g. 'June 01'), '%j' (e.g. '152'), or integer day of year (0 to 365)
 - ***'config' > 'growth' > 'persistence' > 'end_day'*** -- *optional* -- Formatted as '%m-%d' (e.g. '12-31'), '%b %d' (e.g. 'Dec 31'), '%B %d' (e.g. 'December 31'), '%j' (e.g. '365'), or integer day of year (0 to 365)

### findmetdata

 - ***'config' > 'findmetdata' > 'met_root_dir'*** -- *required* --
 - ***'config' > 'findmetdata' > 'time_window' > 'first_hour'*** -- *required* if fire activity data isn't defined --
 - ***'config' > 'findmetdata' > 'time_window' > 'last_hour'*** -- *required* if fire activity data isn't defined --
 - ***'config' > 'findmetdata' > 'met_format'*** -- *optional* -- defaults to 'arl'
 - ***'config' > 'findmetdata' > 'wait' > 'strategy'*** -- *required* if 'wait' section is defined -- 'fixed' or 'backoff'
 - ***'config' > 'findmetdata' > 'wait' > 'time'*** -- *required* if 'wait' section is defined -- time to wait until next attempt (initial wait only if backoff)
 - ***'config' > 'findmetdata' > 'wait' > 'max_attempts'*** -- *required* if 'wait' section is defined  -- max number of attempts
 - ***'config' > 'findmetdata' > 'skip_failures'*** -- *optional* -- default `false`; if true ignore and move on to next module; else, raise exception (default)

#### if arl:
 - ***'config' > 'findmetdata' > 'arl' > 'index_filename_pattern'*** -- *optional* -- defaults to 'arl12hrindex.csv'
 - ***'config' > 'findmetdata' > 'arl' > 'max_days_out'*** -- *optional* -- defaults to 4
 - ***'config' > 'findmetdata' > 'arl' > 'accepted_forecasts'*** -- *optional*  -- initialization times of forecasts to accept met data from (e.g. `["20190725", "2019072600", "2019072700"]` or `["2019-07-27T00:00:00"]`; note that 00Z is assumed if hours are not specified)

### localmet

 - ***'config' > 'localmet' > 'time_step'*** -- *optional* -- hour per arl file time step; defaults to 1
 - ***'config' > 'localmet' > 'skip_failures'*** -- *optional* -- default `true`; if true (default) ignore and move on to next module; else, raise exception
 - ***'config' > 'localmet' > 'working_dir'*** -- *optional* -- default is to create a temp dir; directory to contain profile executable's input and output files
 - ***'config' > 'localmet' > 'delete_working_dir_if_no_error'*** -- *optional* -- default true

### timeprofile

 - ***'config' > 'timeprofile' > 'hourly_fractions'*** -- *optional* -- custom hourly fractions (either 24-hour fractions or for the span of the activity window)
 - ***'config' > 'timeprofile' > 'model'*** -- *optional* -- default: "default"; only used if you want to use the 'ubc-bsf-feps' model

#### If running ubc-bsf-feps model:

 - ***'config' > 'timeprofile' > 'ubc-bsf-feps' > 'interpolation_type'*** -- *optional* -- default: 1
 - ***'config' > 'timeprofile' > 'ubc-bsf-feps' > 'normalize'*** -- *optional* -- default: True
 - ***'config' > 'timeprofile' > 'ubc-bsf-feps' > 'working_dir'*** -- *optional* -- default: None
 - ***'config' > 'timeprofile' > 'ubc-bsf-feps' > 'delete_working_dir_if_no_error'*** -- *optional* -- default true


### plumerise

 - ***'config' > 'plumerise' > 'model'*** -- *optional* -- plumerise model; defaults to "feps"

#### If running feps model:

 - ***'config' > 'plumerise' > 'feps' > 'working_dir'*** -- *optional* -- default: None
 - ***'config' > 'plumerise' > 'feps' > 'delete_working_dir_if_no_error'*** -- *optional* -- default: True
 - ***'config' > 'plumerise' > 'feps' > 'load_heat'*** -- *optional* -- default: False


#### if feps:

 - ***'config' > 'plumerise' > 'feps' > 'feps_weather_binary'*** -- *optional* -- defaults to "feps_weather"
 - ***'config' > 'plumerise' > 'feps' > 'feps_plumerise_binary'*** -- *optional* -- defaults to "feps_plumerise"
 - ***'config' > 'plumerise' > 'feps' > 'plume_top_behavior'*** -- *optional* -- how to model plume top; options: 'Briggs', 'FEPS', 'auto'; defaults to 'auto'
 - ***'config' > 'plumerise' > 'feps' > 'working_dir'*** -- *optional* -- where to write intermediate files; defaults to writing to tmp dir
 - ***'config' > 'plumerise' > 'feps' > 'delete_working_dir_if_no_error'*** -- *optional* -- default true

#### if sev:

 - ***'config' > 'plumerise' > 'sev' > 'alpha'*** -- *optional* -- default: 0.24
 - ***'config' > 'plumerise' > 'sev' > 'beta'*** -- *optional* -- default: 170
 - ***'config' > 'plumerise' > 'sev' > 'ref_power'*** -- *optional* -- default: 1e6
 - ***'config' > 'plumerise' > 'sev' > 'gamma'*** -- *optional* -- default: 0.35
 - ***'config' > 'plumerise' > 'sev' > 'delta'*** -- *optional* -- default: 0.6
 - ***'config' > 'plumerise' > 'sev' > 'ref_n'*** -- *optional* -- default: 2.5e-4
 - ***'config' > 'plumerise' > 'sev' > 'gravity'*** -- *optional* -- default: 9.8
 - ***'config' > 'plumerise' > 'sev' > 'plume_bottom_over_top'*** -- *optional* -- default: 0.5


### extrafiles

- ***'config' > 'extrafiles' > 'dest_dir'*** -- *required* -- where to write extra files
- ***'config' > 'extrafiles' > 'sets'*** -- *optional* (though nothing happens if not defined) -- array of file sets to write

#### if writing emissionscsv:

- ***'config' > 'extrafiles' > 'emissionscsv' > 'filename'*** -- *required* --

#### if writing firescsvs:

- ***'config' > 'extrafiles' > 'firescsvs' > 'fire_locations_filename'*** -- *optional* -- default: 'fire_locations.csv'
- ***'config' > 'extrafiles' > 'firescsvs' > 'fire_events_filename'*** -- *optiona* -- default: 'fire_events.csv'


### trajectories

 - ***'config' > 'trajectories' > 'model'*** -- *optional* -- default: "hysplit"
 - ***'config' > 'trajectories' > 'start'*** -- *required* --
 - ***'config' > 'trajectories' > 'num_hours'*** -- *optional* -- default: 24
 - ***'config' > 'trajectories' > 'output_dir'*** -- *required* -- where output json and geojson files will be written
 - ***'config' > 'trajectories' > 'working_dir'*** -- *optional* -- default is to create a temp dir
 - ***'config' > 'trajectories' > 'delete_working_dir_if_no_error'*** -- *optional* -- default true
 - ***'config' > 'trajectories' > 'handle_existing'*** -- *optional* -- "fail"

#### if running hysplit trajectories:

 - ***'config' > 'trajectories' > 'hysplit' > 'binary'*** -- *optional* -- default: 'hyts_std'
 - ***'config' > 'trajectories' > 'hysplit' > 'start_hours'*** -- *optional* -- default: [0]
 - ***'config' > 'trajectories' > 'hysplit' > 'heights'*** -- *optional* -- default: [10, 100, 1000]
 - ***'config' > 'trajectories' > 'hysplit' > 'vertical_motion'*** -- *optional* -- default: 0 (0 = from met file)
 - ***'config' > 'trajectories' > 'hysplit' > 'top_of_model_domain'*** -- *optional* -- default: 10000
 - ***'config' > 'trajectories' > 'hysplit' > 'output_file_name'*** -- *optional* -- default: "tdump"
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params'*** -- *optional* -- default: {
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_tpot'*** -- *optional* -- default: 1
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_tamb'*** -- *optional* -- default: 1
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_rain'*** -- *optional* -- default: 1
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_mixd'*** -- *optional* -- default: 1
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_relh'*** -- *optional* -- default: 1
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_dswf'*** -- *optional* -- default: 1
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'tm_terr'*** -- *optional* -- default: 0
 - ***'config' > 'trajectories' > 'hysplit' > 'setup_file_params' > 'kmsl'*** -- *optional* -- default: 0
 - ***'config' > 'trajectories' > 'hysplit' > 'static_files' > 'ASCDATA_FILE'*** -- optional -- default files included in bluesky package
 - ***'config' > 'trajectories' > 'hysplit' > 'static_files' > 'LANDUSE_FILE'*** -- optional -- default files included in bluesky package
 - ***'config' > 'trajectories' > 'hysplit' > 'static_files' > 'ROUGLEN_FILE'*** -- optional -- default files included in bluesky package
 - ***'config' > 'trajectories' > 'hysplit' > 'static_files' > 'TERRAIN_FILE'*** -- optional -- default files included in bluesky package


### dispersion

 - ***'config' > 'dispersion' > 'start'*** -- *required* (unless it can be determined from fire activity windows) -- modeling start time (ex. "2015-01-21T00:00:00Z"); 'today' is also recognized, in which case start is set to midnight of the current utc date
 - ***'config' > 'dispersion' > 'num_hours'*** -- *required* (unless it can be determined from fire activity windows) -- number of hours in model run
 - ***'config' > 'dispersion' > 'output_dir'*** -- *required* -- directory to contain output
 - ***'config' > 'dispersion' > 'working_dir'*** -- *required* -- directory to contain working output
 - ***'config' > 'dispersion' > 'delete_working_dir_if_no_error'*** -- *optional* -- default true
 - ***'config' > 'dispersion' > 'model'*** -- *optional* -- dispersion model; defaults to "hysplit"
 - ***'config' > 'dispersion' > 'handle_existing'*** - *optional* -- how to handle case where output dir already exists; options: 'replace', 'write_in_place', 'fail'; defaults to 'fail'
 - ***'config' > 'dispersion' > 'plume_merge' > 'grid' > 'spacing'*** -- *optional*, but required if other plume_merge grid fields are specified -- grid cell dimensions ***in degrees***
 - ***'config' > 'dispersion' > 'plume_merge' > 'grid' > 'boundary' > 'sw' > 'lat'*** -- *optional*, but required if other plume_merge grid fields are specified --
 - ***'config' > 'dispersion' > 'plume_merge' > 'grid' > 'boundary' > 'sw' > 'lng'*** -- *optional*, but required if other plume_merge grid fields are specified --
 - ***'config' > 'dispersion' > 'plume_merge' > 'grid' > 'boundary' > 'ne' > 'lat'*** -- *optional*, but required if other plume_merge grid fields are specified --
 - ***'config' > 'dispersion' > 'plume_merge' > 'grid' > 'boundary' > 'ne' > 'lng'*** -- *optional*, but required if other plume_merge grid fields are specified --

#### if running hysplit dispersion:

 - ***'config' > 'dispersion' > 'hysplit' > 'skip_invalid_fires'*** -- *optional* -- skips fires lacking data necessary for hysplit; default behavior is to raise an exception that stops the bluesky run
 - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'spacing'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed -- grid cell dimensions ***in km unless 'projection' is 'LatLng' (see below)***
 - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'projection'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed -- default: 'LatLng' (which means the spacing is in degrees)
 - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'sw' > 'lat'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
 - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'sw' > 'lng'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
 - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'ne' > 'lat'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
 - ***'config' > 'dispersion' > 'hysplit' > 'grid' > 'boundary' > 'ne' > 'lng'*** -- *required* if grid is not defined in met data or by USER_DEFINED_GRID settings, and it's not being computed --
 - ***'config' > 'dispersion' > 'hysplit' > 'COMPUTE_GRID'*** -- *required* to be set to true if grid is not defined in met data, in 'grid' setting, or by USER_DEFINED_GRID settings -- whether or not to compute grid
 - ***'config' > 'dispersion' > 'hysplit' > 'GRID_LENGTH'***
 - ***'config' > 'dispersion' > 'hysplit' > 'CONVERT_HYSPLIT2NETCDF'*** -- *optional* -- default: true
 - ***'config' > 'dispersion' > 'hysplit' > 'output_file_name'*** -- *optional* -- default: 'hysplit_conc.nc'
 - ***'config' > 'dispersion' > 'hysplit' > 'archive_tranche_files'*** -- *optional* -- copy hysplit input and output files for tranched runs from working dir to output dir; default: false
 - ***'config' > 'dispersion' > 'hysplit' > 'archive_pardump_files'*** -- *optional* -- copy hysplit pardump files to output dir; default: false
 - ***'config' > 'dispersion' > 'hysplit' > 'ensure_dummy_fire'*** -- *optional* -- Ensure that each hysplit process has a dummy fire (at the center of the dispersion grid), to in turn ensure that there's at least one fire within the disperion met domain; Note that some processes may still have a dummy fire, specifically if tranching and there are fewer fires than tranches; default: true


 ####### Config settings adopted from BlueSky Framework

 - ***'config' > 'dispersion' > 'hysplit' > 'DISPERSION_OFFSET'*** -- *optional* -- number of hours to offset start of dispersion
 - ***'config' > 'dispersion' > 'hysplit' > 'ASCDATA_FILE'*** -- *optional* -- default: use default file in package
 - ***'config' > 'dispersion' > 'hysplit' > 'CENTER_LATITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none
 - ***'config' > 'dispersion' > 'hysplit' > 'CENTER_LONGITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none
 - ***'config' > 'dispersion' > 'hysplit' > 'DELT'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'DISPERSION_FOLDER'*** -- *optional* -- default: "./input/dispersion"
 - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_DIFFUSIVITY'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_EFF_HENRY'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_MOL_WEIGHT'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_REACTIVITY'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'DRY_DEP_VELOCITY'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'FIRE_INTERVALS'*** -- *optional* -- default: [0, 100, 200, 500, 1000]
 - ***'config' > 'dispersion' > 'hysplit' > 'HEIGHT_LATITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none
 - ***'config' > 'dispersion' > 'hysplit' > 'ICHEM'*** -- *optional* -- default: 0; options:
   - 0 -> none
   - 1 -> matrix
   - 2 -> 10% / hour
   - 3 -> PM10 dust storm simulation
   - 4 -> Set concentration grid identical to the meteorology grid (not in GUI)
   - 5 -> Deposition Probability method
   - 6 -> Puff to Particle conversion (not in GUI)
   - 7 -> Surface water pollutant transport
 - ***'config' > 'dispersion' > 'hysplit' > 'INITD'*** -- *optional* -- default: 0
   - 0 -> horizontal & vertical particle
   - 1 -> horizontal gaussian puff, vertical top hat puff
   - 2 -> horizontal & vertical top hat puff
   - 3 -> horizontal gaussian puff, verticle particle
   - 4 -> horizontal top hat puff, verticle particle
 - ***'config' > 'dispersion' > 'hysplit' > 'KHMAX'*** -- *optional* -- default: 72
 - ***'config' > 'dispersion' > 'hysplit' > 'LANDUSE_FILE'*** -- *optional* -- default: use default file in package
 - ***'config' > 'dispersion' > 'hysplit' > 'MAKE_INIT_FILE'*** -- *optional* -- default: false
 - ***'config' > 'dispersion' > 'hysplit' > 'MAXPAR'*** -- *optional* -- default: 10000
 - ***'config' > 'dispersion' > 'hysplit' > 'MAX_SPACING_LONGITUDE'*** -- *optional* -- default: 0.5
 - ***'config' > 'dispersion' > 'hysplit' > 'MAX_SPACING_LATITUDE'*** -- *optional* -- default: 0.5
 - ***'config' > 'dispersion' > 'hysplit' > 'MGMIN'*** -- *optional* -- default: 10
 - ***'config' > 'dispersion' > 'hysplit' > 'MPI'*** -- *optional* -- default: false
 - ***'config' > 'dispersion' > 'hysplit' > 'NCPUS'*** -- *optional* -- default: 1
 - ***'config' > 'dispersion' > 'hysplit' > 'NCYCL'*** -- *optional* -- default: 0
 - ***'config' > 'dispersion' > 'hysplit' > 'NDUMP'*** -- *optional* -- default: 0
 - ***'config' > 'dispersion' > 'hysplit' > 'NFIRES_PER_PROCESS'*** -- *optional* -- default: -1 (i.e. no tranching)
 - ***'config' > 'dispersion' > 'hysplit' > 'NINIT'*** -- *optional* -- default: 0
 - ***'config' > 'dispersion' > 'hysplit' > 'NPROCESSES'*** -- *optional* -- default: 1 (i.e. no tranching)
 - ***'config' > 'dispersion' > 'hysplit' > 'NPROCESSES_MAX'*** -- *optional* -- default: -1  (i.e. no tranching)
 - ***'config' > 'dispersion' > 'hysplit' > 'NUMPAR'*** -- *optional* -- default: 1000
 - ***'config' > 'dispersion' > 'hysplit' > 'KBLT'*** -- *optional* -- Vertical Turbulence;  default: 2
 - ***'config' > 'dispersion' > 'hysplit' > 'KDEF'*** -- *optional* -- Horizontal Turbulence;  default: 0
 - ***'config' > 'dispersion' > 'hysplit' > 'KBLS'*** -- *optional* -- Boundary Layer Stability;  default: 1
 - ***'config' > 'dispersion' > 'hysplit' > 'KZMIX'*** -- *optional* -- Vertical Mixing Profile;  default: 0
   - `0` - NONE Vertical diffusivity in PBL varies w/height (DEFAULT)
   - `1` - vertical diffusivity in PBL single average value
   - `2` - scale boundary-layer values multiplied by TVMIX
   - `3` - scall free-troposphere values multiplied by TVMIX
 - ***'config' > 'dispersion' > 'hysplit' > 'TVMIX'*** -- *optional* -- default: 1.0
 - ***'config' > 'dispersion' > 'hysplit' > 'KMIXD'*** -- *optional* -- Mixed Layer Depth Computation; controls how the boundary layer depth is computed;  default: 0
   - `0` - Use met model MIXD if avaialable (DEFAULT)
   - `1` - Copmute from temp profile
   - `2` - Compute from TKE profile
   - `3` - Compute from modified Richardson number (STILT mode default)  (new in hysplit v5.0.0)
   - `>= 10` - use this value as a constant
 - ***'config' > 'dispersion' > 'hysplit' > 'KMIX0'*** -- *optional* -- minimum mixing depth;  default: 150
 - ***'config' > 'dispersion' > 'hysplit' > 'OPTIMIZE_GRID_RESOLUTION'*** -- *optional* -- default: false
 - ***'config' > 'dispersion' > 'hysplit' > 'PARTICLE_DENSITY'*** -- *optional* -- default: 1.0
 - ***'config' > 'dispersion' > 'hysplit' > 'PARTICLE_DIAMETER'*** -- *optional* -- default: 1.0
 - ***'config' > 'dispersion' > 'hysplit' > 'PARTICLE_SHAPE'*** -- *optional* -- default: 1.0
 - ***'config' > 'dispersion' > 'hysplit' > 'PARINIT'*** -- *optional* -- default: "./input/dispersion/PARINIT"
 - ***'config' > 'dispersion' > 'hysplit' > 'PARDUMP'*** -- *optional* -- default: "./input/dispersion/PARDUMP"
 - ***'config' > 'dispersion' > 'hysplit' > 'QCYCLE'*** -- *optional* -- default: 1.0
 - ***'config' > 'dispersion' > 'hysplit' > 'RADIOACTIVE_HALF_LIVE'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'ROUGLEN_FILE'*** -- *optional* -- default: use default file in package
 - ***'config' > 'dispersion' > 'hysplit' > 'SAMPLING_INTERVAL_HOUR'*** -- *optional* -- default: 1
 - ***'config' > 'dispersion' > 'hysplit' > 'SAMPLING_INTERVAL_MIN '*** -- *optional* -- default: 0
 - ***'config' > 'dispersion' > 'hysplit' > 'SAMPLING_INTERVAL_TYPE'*** -- *optional* -- default: 0
 - ***'config' > 'dispersion' > 'hysplit' > 'SMOLDER_HEIGHT'*** -- *optional* -- default: 10.0
 - ***'config' > 'dispersion' > 'hysplit' > 'SPACING_LATITUDE'*** -- *required* if either COMPUTE_GRID or USER_DEFINED_GRID is true
 - ***'config' > 'dispersion' > 'hysplit' > 'SPACING_LONGITUDE'*** -- *required* if either COMPUTE_GRID or USER_DEFINED_GRID is true
 - ***'config' > 'dispersion' > 'hysplit' > 'STOP_IF_NO_PARINIT'*** -- *optional* -- default: True
 - ***'config' > 'dispersion' > 'hysplit' > 'TOP_OF_MODEL_DOMAIN'*** -- *optional* -- default: 30000.0
 - ***'config' > 'dispersion' > 'hysplit' > 'TRATIO'*** -- *optional* -- default: 0.75
 - ***'config' > 'dispersion' > 'hysplit' > 'USER_DEFINED_GRID'*** -- *required* to be set to true if grid is not defined in met data or in 'grid' settings, and it's not being computed -- default: False
 - ***'config' > 'dispersion' > 'hysplit' > 'VERTICAL_EMISLEVELS_REDUCTION_FACTOR'*** -- *optional* -- default: 1
 - ***'config' > 'dispersion' > 'hysplit' > 'SUBHOUR_EMISSIONS_REDUCTION_INTERVAL'*** -- *optional* -- Factor for subhour emissions interval - e.g. 1 (hourly - default), 2 (30 min), etc.; default: 1
 - ***'config' > 'dispersion' > 'hysplit' > 'EMISSIONS_RATE'*** -- *optional* -- default: 0.001
 - ***'config' > 'dispersion' > 'hysplit' > 'VERTICAL_LEVELS'*** -- *optional* -- default: [100]
 - ***'config' > 'dispersion' > 'hysplit' > 'VERTICAL_METHOD'*** -- *optional* -- default: "DATA"
 - ***'config' > 'dispersion' > 'hysplit' > 'WET_DEP_ACTUAL_HENRY'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'WET_DEP_BELOW_CLOUD_SCAV'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'WET_DEP_IN_CLOUD_SCAV'*** -- *optional* -- default: 0.0
 - ***'config' > 'dispersion' > 'hysplit' > 'WIDTH_LONGITUDE'*** -- *required if USER_DEFINED_GRID==true* -- default: none

Note about the grid:  There are three ways to specify the dispersion grid.
If USER_DEFINED_GRID is set to true, hysplit will expect BlueSky framework's
user defined grid settings ('CENTER_LATITUDE', 'CENTER_LONGITUDE',
'WIDTH_LONGITUDE', 'HEIGHT_LATITUDE', 'SPACING_LONGITUDE', and
'SPACING_LONGITUDE').  Otherwise, it will look in 'config' > 'dispersion' >
'hysplit' > 'grid' for 'boundary', 'spacing', and 'projection' fields.  If not
defined, it will look for 'boundary', 'spacing', and 'projection' in the top level
'met' object.

#### if running vsmoke dispersion:

 - ***'config' > 'dispersion' > 'vsmoke' > 'TEMP_FIRE' -- temperature of fire (F), default: 59.0
 - ***'config' > 'dispersion' > 'vsmoke' > 'PRES'*** -- *optional* -- Atmospheric pressure at surface (mb); default: 1013.25
 - ***'config' > 'dispersion' > 'vsmoke' > 'IRHA'*** -- *optional* -- Period relative humidity; default: 25
 - ***'config' > 'dispersion' > 'vsmoke' > 'LTOFDY'*** -- *optional* -- Is fire before sunset?; default: True
 - ***'config' > 'dispersion' > 'vsmoke' > 'STABILITY'*** -- *optional* -- Period instability class - 1 -> extremely unstable; 2 -> moderately unstable; 3 -> slightly unstable; 4 -> near neutral; 5 -> slightly stable; 6 -> moderately stable; 7 -> extremely stable; default: 4
 - ***'config' > 'dispersion' > 'vsmoke' > 'MIX_HT'*** -- *optional* -- Period mixing height (m); default: 1500.0
 - ***'config' > 'dispersion' > 'vsmoke' > 'OYINTA'*** -- *optional* -- Period's initial horizontal crosswind dispersion at the source (m); default: 0.0
 - ***'config' > 'dispersion' > 'vsmoke' > 'OZINTA'*** -- *optional* -- Period's initial vertical dispersion at the surface (m); default: 0.0
 - ***'config' > 'dispersion' > 'vsmoke' > 'BKGPMA'*** -- *optional* -- Period's background PM (ug/m3); default: 0.0
 - ***'config' > 'dispersion' > 'vsmoke' > 'BKGCOA'*** -- *optional* -- Period's background CO (ppm); default: 0.0
 - ***'config' > 'dispersion' > 'vsmoke' > 'THOT'*** -- *optional* -- Duration of convective period of fire (decimal hours); default: 4
 - ***'config' > 'dispersion' > 'vsmoke' > 'TCONST'*** -- *optional* -- Duration of constant emissions period (decimal hours); default: 4
 - ***'config' > 'dispersion' > 'vsmoke' > 'TDECAY'*** -- *optional* -- Exponential decay constant for smoke emissions (decimal hours); default: 2
 - ***'config' > 'dispersion' > 'vsmoke' > 'EFPM'*** -- *optional* -- Emission factor for PM2.5 (lbs/ton); default: 30
 - ***'config' > 'dispersion' > 'vsmoke' > 'EFCO'*** -- *optional* -- Emission factor for CO (lbs/ton); default: 250
 - ***'config' > 'dispersion' > 'vsmoke' > 'ICOVER'*** -- *optional* -- Period's cloud cover (tenths); default: 0
 - ***'config' > 'dispersion' > 'vsmoke' > 'CEIL'*** -- *optional* -- Period's cloud ceiling height (feet); default: 99999
 - ***'config' > 'dispersion' > 'vsmoke' > 'CC0CRT'*** -- *optional* -- Critical contrast ratio for crossplume visibility estimates; default: 0.02
 - ***'config' > 'dispersion' > 'vsmoke' > 'VISCRT'*** -- *optional* -- Visibility criterion for roadway safety; default: 0.125
 - ***'config' > 'dispersion' > 'vsmoke' > 'GRAD_RISE'*** -- *optional* -- Plume rise: TRUE -> gradual to final ht; FALSE ->mediately attain final ht; default: True
 - ***'config' > 'dispersion' > 'vsmoke' > 'RFRC'*** -- *optional* -- Proportion of emissions subject to plume rise; default: -0.75
 - ***'config' > 'dispersion' > 'vsmoke' > 'EMTQR'*** -- *optional* -- Proportion of emissions subject to plume rise for each period; default: -0.75
 - ***'config' > 'dispersion' > 'vsmoke' > 'KMZ_FILE'*** -- *optional* -- default: "smoke_dispersion.kmz"
 - ***'config' > 'dispersion' > 'vsmoke' > 'OVERLAY_TITLE'*** -- *optional* -- default: "Peak Hourly PM2.5"
 - ***'config' > 'dispersion' > 'vsmoke' > 'LEGEND_IMAGE'*** -- *optional* -- absolute path nem to legend; default: "aqi_legend.png" included in bluesky package
 - ***'config' > 'dispersion' > 'vsmoke' > 'JSON_FILE'*** -- *optional* -- name of file to write GeoJSON dispersion data; default: "smoke_dispersion.json"
 - ***'config' > 'dispersion' > 'vsmoke' > 'CREATE_JSON'*** -- *optional* -- whether or not to create the GeoJSON file; default: True
 - ***'config' > 'dispersion' > 'vsmoke' > 'DUTMFE'*** -- *optional* -- UTM displacement of fire east of reference point; default: 0
 - ***'config' > 'dispersion' > 'vsmoke' > 'DUTMFN'*** -- *optional* -- UTM displacement of fire north of reference point; default: 100
 - ***'config' > 'dispersion' > 'vsmoke' > 'XBGN'*** -- *optional* -- What downward distance to start calculations (km); default: 150
 - ***'config' > 'dispersion' > 'vsmoke' > 'XEND'*** -- *optional* -- What downward distance to end calculation (km) - 200km max; default: 200
 - ***'config' > 'dispersion' > 'vsmoke' > 'XNTVL'*** -- *optional* -- Downward distance interval (km) - 0 results in default 31 distances; default: 0.05
 - ***'config' > 'dispersion' > 'vsmoke' > 'TOL'*** -- *optional* -- Tolerance for isopleths; detault: 0.1

### visualization

 - ***'config' > 'visualization' > 'targets'*** -- *optional* -- defaults to dispersion

#### if visualizing hysplit dispersion:

 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'smoke_dispersion_kmz_filename'*** -- *optional* -- defaults to 'smoke_dispersion.kmz'
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'fire_kmz_filename'*** -- *optional* -- defaults to 'smoke_dispersion.kmz'
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'fire_locations_csv_filename'*** -- *optional* -- defaults to 'fire_locations.csv'
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'fire_events_csv_filename'*** -- *optional* -- defaults to 'fire_events.csv'
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'layers'*** -- *optional* -- defaults to [0]
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'prettykml'*** -- *optional* -- whether or not to make the kml human readable; defaults to false
 - ***'config' > 'visualization' >  'hysplit' > 'output_dir' -- *optional* -- where to create visualization output; if not specified, visualization output will go in hysplit output directory
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'images_dir' -- *optional* -- sub-directory to contain images (relative to output direcotry); default is 'graphics/''
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'data_dir' -- *optional* -- sub-directory to contain data files (relative to output direcotry); default is output directory root
 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'create_summary_json'*** -- *optional* -- default False

 - ***'config' > 'visualization' > 'dispersion' > 'hysplit' > 'blueskykml_config'*** -- *optional* -- contains configuration to pass directly into blueskykml; expected to be nested with top level section keys and second level option keys; see https://github.com/pnwairfire/blueskykml/ for configuration options

#### if visualizing hysplit trajectories:

 - ***'config' > 'visualization' > 'trajectories' > 'hysplit' > 'kml_file_name'*** -- *optional* -- defaults to 'hysplit-trajectories.kml'

### export

- ***'config' > 'export' > 'modes'*** -- *optional* -- defaults to []
- ***'config' > 'export' > 'extra_exports'*** -- *optional* -- array of extra output files to export (ex. 'dispersion' or 'visualization' outputs); defaults to none

#### if using email:

- ***'config' > 'export' > 'email' > 'recipients'*** -- *required* --
- ***'config' > 'export' > 'email' > 'sender'*** -- *optional* -- defaults to 'bsp@airfire.org'
- ***'config' > 'export' > 'email' > 'subject'*** -- *optional* -- defaults to 'bluesky run output'
- ***'config' > 'export' > 'email' > 'smtp_server'*** -- *optional* -- defaults to 'localhost'
- ***'config' > 'export' > 'email' > 'smtp_port'*** -- *optional* -- defaults to 1025
- ***'config' > 'export' > 'email' > 'smtp_starttls'*** -- *optional* -- defaults to False
- ***'config' > 'export' > 'email' > 'username'*** -- *optional* --
- ***'config' > 'export' > 'email' > 'password'*** -- *optional* --

#### if saving locally, uploading, or publishing to AWS S3:

 - ***'config' > 'export' > ['localsave'|'upload'] > 'output_dir_name'*** -- *optional* -- defaults to run_id, which is generated if not defined
 - ***'config' > 'export' > ['localsave'|'upload'] > 'extra_exports_dir_name'*** -- *optional* -- generated from extra_exports mode name(s) if not defined
 - ***'config' > 'export' > ['localsave'|'upload'] > 'json_output_filename'*** -- *optional* -- defaults to 'output.json'

#### if saving locally:

 - ***'config' > 'export' > 'localsave' > 'dest_dir'*** - *required* -- destination directory to contain output directory
 - ***'config' > 'export' > 'localsave' > 'handle_existing'*** - *optional* -- how to handle case where output dir already exists; options: 'replace', 'write_in_place', 'fail'; defaults to 'fail'

#### if uploading:

 - ***'config' > 'export' > 'upload' > 'tarball_name'*** - *optional* -- defaults to '<output_dir>.tar.gz'
 - ***'config' > 'export' > 'upload' > 'scp' > 'host'*** - *required* if uploading via scp (which is currently the only supported upload mode) -- hostname of server to scp to
 - ***'config' > 'export' > 'upload' > 'scp' > 'user'*** - *optional* if uploading via scp (which is currently the only supported upload mode) -- username to use in scp; defaults to 'bluesky'
 - ***'config' > 'export' > 'upload' > 'scp' > 'port'*** - *optional* if uploading via scp (which is currently the only supported upload mode) -- port to use in scp; defaults to 22
 - ***'config' > 'export' > 'upload' > 'scp' > 'dest_dir'*** - *required* if uploading via scp (which is currently the only supported upload mode) -- destination directory on remote host to contain output directory

#### if publishing to AWS S3

 - ***'config' > 'export' > 's3' > 'bucket'*** - *required* if publishing to s3 -- destination AWS S3 bucket
 - ***'config' > 'export' > 's3' > 'key_prefix'*** - *optional* -- key prefix to use if uploading to AWS S3
 - ***'config' > 'export' > 's3' > 'tarball_name'*** - *optional* -- defaults to '<output_dir>.tar.gz'
 - ***'config' > 'export' > 's3' > 'include_tarball'*** - *optional* -- defaults to true; if false, tarball isn't uploaded to S3
 - ***'config' > 'export' > 's3' > 'default_region_name'*** - *optional* -- used if there is a failure to get region name from boto3 S3 client; (region name is only used for recording s3 object url in output data)

##### Note on AWS credentials

AWS credentials and configuration are not specified in the bluesky
configuration. Instead, they are specified in files under  `~/.aws/`.
This includes `~/.aws/credentials`, which looks like this:

```
[default]
aws_access_key_id = ABC123
aws_secret_access_key = XYZ987
```

and `~/.aws/config`, which minimally looks like this:

```
[default]
region=us-west-2
```

If using docker, mount them in the container with something like the following

```
-v $HOME/.aws/:/home/bluesky/.aws/
```

### archive

- ***'config' > 'archive' > 'tarzip'*** -- *optional* -- list of modules whose output directories should be tar'd and zipped and then deleted; defaults empty list

### statuslogging

Bluesky supports posting statuses to statuslogging web service.  The
source code for this service is not yet available, so ignore this section
unless you have access to it.

 - ***'config' > 'statuslogging' > 'enabled'*** - on/off switch
 - ***'config' > 'statuslogging' > 'api_endpoint'*** - i.e. http://HOSTNAME/status-logs/",
 - ***'config' > 'statuslogging' > 'api_key'*** - api key
 - ***'config' > 'statuslogging' > 'api_secret'*** - api secret
 - ***'config' > 'statuslogging' > 'process'*** - how you want to identify the process to the status logger
 - ***'config' > 'statuslogging' > 'domain'*** - how you want to identify the met domain to the status logger


