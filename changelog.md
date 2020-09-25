## 4.0.7
 - Fixed conversion factor for Prichard/ONeill emissions output

## 4.0.8
 - Fixed bug in findmetdata time window merging logic

## 4.0.9
 - Upgrade to geoutils v1.0.3

## 4.0.10
 - Upgrade blueskykml to v2.4.3

## 4.0.11
 - Upgrade met to v1.2.3

## 4.1.0

***Note that this release is not backwards compatible.  Despite this fact, we decided for other reasons to keep the major version 4.***

- configuration
  - 'config' may no longer be specified in the input data; set it in a separate file or via command line args
  - config keys are case insensitive (except for under visualization > hysplit > blueskykml config)
  - a run's configuration is included in the output data under 'run_config'
  - a config file may specify configuration under 'config' or 'run_config' (to allow you to use a previous run's dumped configuration in a subsequent run by passing in the output file as a config file)
  - added --dump-config to show the config settings (defaults + user overrides) of a potential run
  - deprecated FiresManager.get_config_value
  - deprecated FiresManager.set_config_value
  - deprecated FiresManager.config (getter and setter)
  - refactored run_id logic and store as FiresManager attr rather than in _meta dict
- support building docker image with default user matching host user's UID and group id & added script to add user post-build
- CONSUME
  - upgrade consume package to v5
  - capture and ignore consume stdout
  - modify consume input defaults
- emissions
  - Fix conversion factor for Prichard/Oneill emissions output (values wer half of what they should have been)
  - added regression test case for Prichard/Oneill emissions
- various changes to run-all-fuelbeds.py dev script
- findmetdata time window merging logic
- new input data structure
  - 'fire_information' -> 'fires'
  - 'growth' -> 'activity'
  - nested activity organization, with collections and active areas
  - specified_points & perimeter_polygon objects replacing location object
  - remove ingestion module and require clients to structure data correctly
  - remove bsp-csv2json
- support FireSpider v3 output
- rename plumerising module as plumerise
- rename timeprofiling module as timeprofile

## 4.1.1

- added support for loading BSF (BlueSky Framework) fire location csv output data

## 4.1.2

- Fix support for either dict or list for export > upload > scp config setting

## 4.1.3

 - Indicate use of carryover/parinit in dispersion output info and visualization summary.json
 - Make summary.json more human readable with indents
 - Upgrade afscripting to v1.1.5
 - Add custom log level SUMMARY 25
 - add SUMMARY level messages: bluesky version, input file, output file, 'Run complete', fire counts, 'Modules to be run: ...', 'Running module ...'

## 4.1.4
 - Support specifying target WebSky version summary.json

## 4.1.5
 - Support all 3.*.* fire spider versions

## 4.1.6
 - Upgrade eflookup to v3.1.2 to get updated Prichard-Oneill emissions factors

## 4.1.7
 - List ARL files in order in the hysplit CONTROL file
 - Support filtering activity by start and/or end times

## 4.1.8
 - Fix bug in hysplit code where, when using tranches, all fires were being run in each tranche

## 4.1.9
 - distribute fire locations evenly in tranches, ignoring parent fires

## 4.1.10
 - Support restricting findmetdata to specific allowed forecasts (e.g. to allow 2019-07-31 00Z met data but not 2019-07-30 00Z for a 7/31 run)

## 4.1.11
 - Added bsp-run-info script

## 4.1.12
 - Initial version of bsp-output-visualizer

## 4.1.13
 - Minor updates to build-docker-image
 - Second version of bsp-output-visualizer
 - Refactored configuration management to be thread safe (to be able to execute parallel runs with different configurations in separate threads)

## 4.1.14
 - bug fix and added error handling

## 4.1.15
 - New smokeready extrafiles module

## 4.1.16
 - Upgrade met to v1.2.4

## 4.1.17
 - Merge dispersion fire objects to reduce number of zero-emissions points

## 4.1.18
 - Don't group fires into sets before tranching for hysplit
 - Updates in smokeready extrafiles module

## 4.1.19
 - Upgrade met to v1.2.5

## 4.1.20
 - Handle comparison of string and datetime objects when merging fires for dispersion

## 4.1.21
 - Added data error handling in smokeready extrafiles module

## 4.1.22
 - Added `archive` module, which currently supports creating zipped tarballs of module-specific output directories (dispersion, plumerise, extrafiles, etc.), and then deleting the original directory

## 4.1.23
 - Fixed bug where tranched hysplit threads where using configuration defaults, ignoring configuration overrides specified by user
 - Fixed adhoc pardump / parinit hysplit test

## 4.1.24
 - add status log post with dispersion fire location count

## 4.1.25
 - Support replacing '{run_id}' in log file name
 - Add option to merge fires (i.e. modeled plumes) by configured grid cell in despersion module
 - other minor updates

## 4.1.26
 - Updated bsp-run-info to include count of plumes modeled in dispersion

## 4.1.27
 - Modify and add to dispersion module's reporting on fire, location, and plume counts
 - Update bsp-run-info to list dispersion fire, location, and plume counts
 - Copy combined hysplit_conc.nc from working dir to output dir for tranched runs; this fixes a bug where only the last processed tranche's output file was being incorporated into KML and dispersion images
 - Only archive tranched hysplit files if configured to do so and use tranche_num as the archived file suffix
 - Fixed bug in adding suffix to archived dispersion files lacking file extension
 - Fixed bug in dispersion file archiving logic where 0 wasn't recognized as a valid, defined suffix
 - Only archive hysplit pardump files if configured to do so

## 4.1.28
 - Fixed two FIPS bugs

## 4.1.29
 - replace location `length_of_ignition` field with active area `ignition_start` and `ignition_end` fields, but retain support for `length_of_ignition` in consumeutils for backwards compatibility
 - Upgrede timeprofile to v1.1.1
 - Add support for FEPS timeprofile, using it for Rx fires unless custom hourly fractions are specified
 - regression test updates

## 4.1.30
 - Upgrede timeprofile to v1.1.2

## 4.1.31
 - Create new class bluesky.io.SubprocessExecutor for running sub-processes and capturing their output, both stdout and stderr, with either real-time or post-execution logging of the output
 - Update dispersion modules (hysplit and vsmoke) as well as export upload module to use bluesky.io.SubprocessExecutor instead of using the subprocess package directly
 - Install ssh in docker image, since it's needed by export upload <-- this fixes the code that creates the remote directory before scping the export tarball
 - consolidate RUN commands in Dockerfile

## 4.1.32
 - Ensure that there's a dummy fire for each hysplit process, to guarantee at least one fire within met domain, thus avoiding hysplit failure resulting from all points falling outside of met domain.
 - Assign zero emissions to dummy hysplit fires

## 4.1.33
 - Bug fix in dispersion code

## 4.1.34
 - Change default emissions model from 'feps' to 'prichard-oneill'
 - Decrease default value for TOP_OF_MODEL_DOMAIN from 30000 to 10000
 - Fix bug in dispersion that was triggered when a fire location had inadequate heat
 - Raise an exception in dispersion if there are no fire locations with valid emissions and heat data

## 4.1.35
 - add trajectories module with support for hysplit model
 - refactor visualization module to support multiple targets and add new 'trajectories' target

## 4.1.36
 - Modify trajectories output info so that it can be recognized as an extra export

## 4.2.0

***Note that this release is not backwards compatible with regards to the output data structure, specifically the 'visualization' section of the output. (Since visualization now supports multiple targets, the hysplit dispersion info is now under "visualization" > "dispersion" > "hysplit" instead of "visualization" > "hysplit"). As with v4.1, we decided to keep the major version 4.***

 - update visualization section of configuration doc
 - modified structure of trajectories output info to nest output dir, file names, etc under 'output' (to support export)
 - modified visualization output info sections (to support multiple targets)
 - fix and add error handling in trajectories and visualization modules
 - Update trajectories module so that run continues even if all trajectories fail, and add warning/error message to trajectories output info if any/all hysplit runs fail

## 4.2.1
 - added error handling to smokeready extrafile writer

## 4.2.2
 - Default skip_failed_fires to true
 - Upgrade eflookup to v3.2.1

## 4.2.3
 - Update bsf load module to optionally load separate timeprofile file

## 4.2.4
 - Update bsf loader to support isoformatted date_time values

## 4.2.5
 - Update BSF loader to store utc_offset in the active area object rather than the specified point

## 4.2.6
 - Upgrade emitcalc to 2.0.2
 - Be specific about python package dependency versions

## 4.2.7
 - Upgrade eflookup to v3.2.2

## 4.2.8
 - Update hysplit trajectories to gracefully handle no fires, and log and record warning
 - Update dispersion to not abort if there no fires

## 4.2.9
 - Add script for creating new version of bluesky
 - Bug fixes in writing of fire_events.csv

## 4.2.10
 - Update base loader and BSF loader to honor `skip_failures`
 - Upgrade `met` package to `v2.0.0` and switch to using bulk localmet profiler

 ## 4.2.11
 - Include source in fire_locations.csv

## 4.2.12
 - Add fuelbed_fractions to fire_locations.csv
 - Update fuelbeds module to support forcing use of AK FCCS fuelbed map
 - Dev script updates

## 4.2.13
 - Update fires csv writer to not fail on integer fccs_id values

## 4.2.14
 - Added support for subhourly emissions in hysplit dispersion
 - Added support for loading and running Canadian fire data through plumerise
 - Refactored use of hysplit dummy fires so that
   1. the number of tranches equals NPROCESSES and
   2. every tranche has a dummy fire (to ensure that there is at least one fire within the dispersion domain for each hysplit process)
 - Added support for loading multiple input files
 - Added support for loading input files over http
 - Upgrade met package to v2.0.1

## 4.2.15
 - Update bsp-run-info to report on total area by UTC date
 - Upgrade plumerise to v2.0.3
 - Add growth module with persistence model

## 4.2.16
 - Upgrade pyairfire to v3.0.5
 - Add option in emissions, plumerise, timeprofile, trajectories, and dispersion modules to delete working dirs if no error is encountered

## 4.2.17
 - fix bug (missing import) in trajectories module
