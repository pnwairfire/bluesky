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
 - Fix bug (missing import) in trajectories module

## 4.2.18
 - Fix bug in hysplit trajectories where only traj lines from last start hour were being saved

## 4.2.19
 - Fix issue in hysplit trajectories causing duplicate trajectories

## 4.2.20
 - Upgrade met package to v2.0.2
 - Upgrade afconfig package to v1.1.3

## 4.2.21
 - Upgrade blueskykml to v3.0.0
 - Add `makepolygons` to repo and docker image
 - Bump hysplit visualization output_version to 2.0.1

## 4.2.22
 - Updated regex used for matching blueskykml legend image file names (which changed in v3.0.0)

## 4.2.23
 - modify error handling logic in hysplit trajectories visualization module
 - Support export to AWS S3

## 4.2.24
 - minor updates to AWS s3 export module
 - updates affecting wildcard replacement in config settings and input file names
 - added parsing of fire location start and end times in dispersion module, in case they're not already loaded into datetime objects

## 4.3.0
 - docker image and bundled binaries built off of ubuntu 20.04 with python 3.8.5; includes code updates and many dependency package upgrades

## 4.3.1
 - Use localmet data, if available, for setting windspeed for CONSUME
 - Set localmet data, if available, for FEPS plumerise
 - Use `mpi-default-bin` and `mpi-default-dev` instead of `libopenmpi-dev` and `openmpi-bin`

## 4.3.2
 - Remove `libmpich-dev` and replace hysplit binaries with newly built ones

## 4.3.3
 - Use `mpich`, `libmpich-dev`, `libmpich12` insead of `mpi-default-bin` and `mpi-default-dev`, and replace mpi hysplit binaries with newly built ones
 - fix bug in persistence growth module when defaulting 'date_to_persist' to run's 'today' variable

## 4.3.4
 - Refactor localmet module to not fail when there are no fires
 - Add new 'ecoregion' module and script 'ecoregion-lookup'

## 4.3.5
 - Update ecoregion module to support default, used when look-up fails
 - Remove ecoregion look-up from consumption module

## 4.3.6
 - Added the following localmet config options:
   - `localmet` > `skip_failures` to ignore failure and move onto next module
   - `localmet` > `working_dir` to specify where to write profile executable's input and output files (require `met` package upgrade to `v3.0.1`)
   - `localmet` > `delete_working_dir_if_no_error` to delete working dir if no error

## 4.3.7
 - skip FIPS lookup in smokeready

## 4.3.8
 - config setting controlling use of default FIPS code in smokeready module
 - new hysplit binaries

## 4.3.9
 - new hysplit binaries
 - fix bsp config options adhoc test
 - upgrade consume to v5.1.1

## 4.3.10
 - Make bsp-run-info more fault tolerant
 - Fix bug in smokeready module
 - Add documentation
 - Add HYSPLIT v5.1 binaries

## 4.3.11
 - Copy HYSPLIT v5.1 to docker image

## 4.3.12
 - More robust fuelbed lookup, automatically handling both AK and lower 48 states
 - Minor tweak to plume merge configuration validation

## 4.3.13
 - Upgrade pyairfire to v4.0.1

## 4.3.14
 - new 'sev-feps' plumerise model, which contains logic to use SEV for each location, if possible, but fall back on FEPS

## 4.3.15
 - support compressed (gzip'd) input and output data
   - inputing from local file, stdin, and remote file over http
   - outputing to local file and stdout
   - exporting to AWS S3

## 4.3.16
 - Improve loading of remote compressed files

## 4.3.17
 - Upgrade blueskykml to v4.0.1
 - Upgrade pyairfire to v4.0.2
 - Update BSF CSV file loader to support loading remote files via http
 - Updates to filtering based on inclusion/exclusion lists

## 4.3.18
 - Update persistence growth module to mark persisted activity
 - Fix issues in smokeready extrafiles module

## 4.3.19
 - Support adding top level 'errors' key to bluesky output
 - Add option `--input-file-failure-tolerance` to allow skipping of some or all input file load failures; default now is to exit execution only if all input files fail to load

## 4.3.20
 - Update localmet bulk profiler

## 4.3.21
 - Upgrade blueskykml to v4.0.2

## 4.3.22
 - Upgrade blueskykml to v4.0.3

## 4.3.23
 - Change default `websky_version` from 1 to 2
 - Update `SubprocessExecutor` to handle unicode errors when reading and logging subprocess output
 - Include runtime info in final status log

## 4.3.24
 - microsecond resolution in status log timestamps

## 4.3.25
 - Ensure that smokeready ids are no greater than 15 characters

## 4.3.26
 - Upgrade met package to v3.0.2

## 4.3.27
 - Update fccs id data check to accept integer value FCCS #0
 - dev script updates

## 4.3.28
 - Add 'fuelmoisture' module, currently supporting NFDRS model for computing 1-hr and 1-hr values, as well as defaults based on fire type
 - Update CONSUME to use fuel moisture data, if available
 - Dev script updates

## 4.3.29
 - Fix bug in applying consume settings

## 4.3.30
 - Upgrade blueskykml to v4.0.4
 - More flexibility in the format of `date_time` when writing/reading `date_time` to/from csv files

## 4.3.31
 - Minor tweak to configurability of formatting `date_time` when writing csv files (support '{utc_offset}' wildcard)

## 4.3.32
 - Fix bug in formatting `date_time` when writing csv files

## 4.3.33
 - Upgrade emitcalc to v3.0.1 and support option to include emissions factors in output data
 - Dev script updates

## 4.3.34
 - Upgrade eflookup to v4.0.2
 - Switch to using latest (SERA) Prichard-O'Neill emissions factors

## 4.3.35
 - Support '%Y%m%d' date_time format in bsf loader

## 4.3.36
 - Upgrade eflookup to v4.0.3

## 4.3.37
 - Allow addition of dummy fire to all hysplit processes to be turned off

## 4.3.38
 - Add HYSPLIT v5.2 binaries

## 4.3.39
 - Support custom emissions rate in hysplit

## 4.3.40
 - Add option --profile-output-file to optionally profile a run

## 4.3.41
 - Update default 1000hr and duff FM values, and add new litter FM defaults
 - Use true litter FM value, not live FM, when running consume

## 4.3.42
 - Update BSF loader to support optionally loading emissions data

## 4.3.43
 - Allocate 70% of BSF loaded emissions to flaming, 20% to smoldering, and 10% to residual

## 4.3.44
 - Don't persist fires of type 'unknown'
 - List 'unknown' instead of 'WF' in fire_locations.csv if type is unknown

## 4.3.45
 - Tweak failure skipping logic in localmet
 - Add support to skip failures in findmetdata

## 4.3.46
 - Updates to persistence growth module
   - Added support for different configurations based on time of year
   - Added support for daily percentages, to allow activity to trail off
   - Added unit tests
   - Other minor updates

## 4.3.47
 - Upgrade fccsmap to v3.0.2

## 4.3.48
 - Fix npm install error
 - Upgrade fccsmap to v3.0.3

## 4.3.49
 - Persistence follow-ups.

## 4.3.50
 - Refactor vertical allocation of emissions for hysplit so that top level has zero.

## 4.3.51
 - fix data type handling in ubcbsffeps timeprofilers and nfdrs fuelmoisture modules

## 4.3.52
 - Support wait/retry logic when loading input files
 - Load input files in parallel
 - Fix broken unit tests

## 4.3.53
 - Update dispersion timeprofile and plumerise logic to work with partial hour UTC offsets

## 4.3.54
 - Update findmetdata to remove any met info from previous run

## 4.3.55
 - Add option fuelbeds > skip_failures

## 4.3.56
 - Update fuelbeds summarization to handle fires with failed look-up

## 4.3.57
 - Update fuelmoisture to support specifying defaults moisture profile

## 4.3.58
 - bug fix in output analysis
 - Upgrade blueskykml to v4.0.5

## 4.3.59
 - fix docker build issue

## 4.3.60
 - Upgrade blueskykml to v4.0.6

## 4.3.61
 - Upgrade eflookup to v4.0.4

## 4.3.62
 - Fix setting of localmet data to reflect each location's time window

## 4.3.63
 - Upgrade fccsmap to v3.0.4

## 4.3.64
 - Upgrade blueskykml to v4.0.7

## 4.3.65
 - Specify all dependencies to avoid docker build issues

## 4.3.66
 - Add HYSPLIT v5.2.3 binaries (patched with fix for metpos errors)

## 4.3.67
 - Add HYSPLIT v5.2.3 binaries to docker image

## 4.3.68
 - Add HYSPLIT v5.1.0 binaries (patched with fix for metpos errors)

## 4.3.69
 - Upgrade blueskykml to v4.0.8

## 4.3.70
 - Upgrade blueskykml to v4.0.9
 - Update hysplit visualization export to handle saved original images

## 4.3.71
 - Update HYSPLIT v5.1.0 and v5.2.3 binaries

## 4.3.72
 - Support specifying constant smoldering fraction in hysplit

## 4.3.73
 - Support new hysplit options related to turbulence-dispersion

## 4.3.74
 - Minor updates to consumption and extrafiles modules

## 4.3.75
 - Support adjusting modeled fuel load and consumption data based on estimated fuel load

## 4.3.76
 - Support adjusting modeled consumption data based on estimated consumption
