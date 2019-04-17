
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
- upgrade consume package to v5
- capture and ignore consume stdout
- various changes to run-all-fuelbeds.py dev script
- Fix conversion factor for Prichard/Oneill emissions output (valyes wer half of what they should have been)
- modify consume input defaults
- update ingestion to pass through more consume input fields
