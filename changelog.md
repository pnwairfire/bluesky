
## 4.1.0

***Note that this release is not backwards compatible.  Despite this fact, we decided for other reasons to keep the major version 4.***

- configuration
 - may no longer be specified in input data - either in a separate file or via command line args
 - run's configuration included in output data under 'run_config'
 - config file may specify configuration under 'config' or 'run_config' (to allow you to use a previous run's configuration in a subsequent run by passing the in the output file in as a config file)
 - added --dump-config to show the config settings (defaults + user verrides) of a potential run
