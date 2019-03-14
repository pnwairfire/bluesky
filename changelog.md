
## 4.1.0

***Note that this release is not backwards compatible.  Despite this fact, we decided for other reasons to keep the major version 4.***

- configuration
  - 'config' may no longer be specified in the input data; set it in a separate file or via command line args
  - config keys are case insensitive
  - a run's configuration is included in the output data under 'run_config'
  - a config file may specify configuration under 'config' or 'run_config' (to allow you to use a previous run's dumped configuration in a subsequent run by passing in the output file as a config file)
  - added --dump-config to show the config settings (defaults + user overrides) of a potential run
  - deprecated FiresManager.get_config_value
  - deprecated FiresManager.set_config_value
  - deprecated FiresManager.config (getter and setter)
