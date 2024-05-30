## Usage:

### bsp

bsp is the main BlueSky executable.  It can be used for either or both of
the following:

 - to filter a set of fires by country code
 - **to run BlueSky modules (consumption, emissions, etc.) on fire data**

#### Getting Help

Use the ```-h``` flag for help:

    $ bsp -h
    Usage: bsp [options] [<module> ...]

    Options:
      -h, --help            show this help message and exit
      -l, --list-modules    lists available modules; order matters
      ...

Use the ```-l``` flag to see available BlueSky modules:

    $ bsp -l

    Available Modules:
            consumption
            emissions
            fuelbeds
            ...

#### Input / Output

The ```bsp``` executable inputs fire json data, and exports a modified version
of that fire json data.  You can input from stdin (via piping or redirecting)
or from file.  Likewise, you can output to stdout or to file.

Example of reading from and writing to file:

    $ bsp -i /path/to/input/fires/json/file.json -o /path/to/output/modified/fires/json/file.json fuelbeds ecoregion consumption

Example of piping in and redirecting output to file

    $ cat /path/to/input/fires/json/file.json | bsp fuelbeds > /path/to/output/modified/fires/json/file.json

Example of redirecting input from and outputing to file:

    $ bsp fuelbeds ecoregion consumption emissions < /path/to/input/fires/json/file.json > /path/to/output/modified/fires/json/file.json

Example of redirecting input from file and outputing to stdout

    $ bsp fuelbeds < /path/to/input/fires/json/file.json

#### Data Format

```bsp``` supports inputting and outputing only json formatted fire data.

#### Piping

As fire data flow through the modules within ```bsp```, the modules add to the
data without modifying what's already defined (with the exception of the
merge, and filter modules, described below, which do modify the data).
Modules further downstream generally work with data produced by upstream
modules, which means that order of module execution does matter.

You can run fires through a series of modules, capture the output, and
then run the output back into ```bsp``` as long as you start with a module
that doesn't depend on data updates made by any module not yet run.  For
example, assume that you start with the following fire data:

    # TODO: fill in new example

Assume that this data is in a file called fires.json, and that you run
it through the fuelbeds module, with the following:

    bsp -i fires.json fuelbeds |python -m json.tool

You would get the following output (which is the input json with the addition
of the 'fuelbeds' array in the fire object, plus 'today', 'runtime', processing' and 'summary'
fields):

    # TODO: fill in output


This output could be piped back into ```bsp``` and run through the consumption
module, like so:

    bsp -i fires.json fuelbeds | bsp consumption

yielding the following augmented output:

    # TODO: fill in output


Though there would be no reason to do so in this situation, you could re-run
the fuelbeds module in the second pass throgh ```bsp```, like so:

    bsp -i fires.json fuelbeds | bsp fuelbeds ecoregion consumption

The second pass through the fuelbeds module would reinitialize the fuelbeds
array created by the first pass through the module. After running through
consumption, you would get the same output as above.  Though this re-running
of the fuelbeds module is pointless in this example, there may be situations
where you'd like to re-run your data through a module without starting from
the beginning of the pipeline.

Here's an example that runs through comsumption, captures the output, then
runs the output back through consumption and on through emissions:

    bsp -i fires.json fuelbeds ecoregion consumption -o fires-c.json
    cat fires-c.json | bsp consumption emissions > fires-e.json

```fires-c.json``` would contain the output listed above.  ```fires-e.json```
would contain this output, agumented with emissions data:

    # TODO: fill in output

##### Pretty-Printing JSON Output

To get indented and formated output like the above examples, try
[json.tool](https://docs.python.org/3.5/library/json.html).  It will
work only if you let the results go to STDOUT.  For example:

    bsp -i fires.json --indent 4 fuelbeds

#### Merge

TODO: fill in this section...

#### Filter

TODO: fill in this section...

#### Notes About Input Fire Data

##### GeoJSON vs. Lat + Lng + Area

One thing to note about the fire data is that the location can be specified by
a single lat/lng pair with area (assumed to be acres) or by perimeter
data, represented by a polygon or multi-polygon.

The following is an example of the former:

    # TODO: fill in new example

while the following is an example of the latter:

    # TODO: fill in new example


#### Log File

`bsp` produces log output, either to file or to stdout.  The log level
is set with the `--log-level` flag.  The log output looks like the following:

```
2019-02-22 06:24:48,191 INFO: BlueSky v4.1.2
2019-02-22 06:24:48,191 INFO: output file: None
2019-02-22 06:24:48,191 INFO: config options: None
2019-02-22 06:24:48,191 INFO: module: []
2019-02-22 06:24:48,191 INFO: log message format: None
2019-02-22 06:24:48,191 INFO: run id: None
2019-02-22 06:24:48,191 INFO: log level: 10
2019-02-22 06:24:48,191 INFO: log file: None
2019-02-22 06:24:48,192 INFO: today: None
2019-02-22 06:24:48,192 INFO: config file options: None
2019-02-22 06:24:48,192 INFO: version: False
2019-02-22 06:24:48,192 INFO: no input: False
2019-02-22 06:24:48,192 INFO: input file: /data/json/1-fire-24hr-20150121-Seattle-WA.json
2019-02-22 06:24:48,192 INFO: indent: None
2019-02-22 06:24:48,192 DEBUG: Status logging disabled - not submitting 'Good','Main', 'Start', {}.
2019-02-22 06:24:48,192 DEBUG: Status logging disabled - not submitting 'Good','Main', 'Finish', {}.
2019-02-22 06:25:25,566 INFO: Running fuelbeds module
2019-02-22 06:25:25,566 DEBUG: Status logging disabled - not submitting 'Good','fuelbeds', 'Finish', {}.
2019-02-22 06:25:25,566 DEBUG: Status logging disabled - not submitting 'Good','Main', 'Finish', {}.
2019-02-22 06:24:48,193 INFO: Fire counts: {'fires': 1}
```



### Other Executables

the bluesky package includes these other executables:

  - bsp-output-visualizer
  - bsp-run-info - extracts information about a bluesky run from it's output
  - bulk_profiler_csv - extracts local met information from multiple locations at once
  - feps_emissions -
  - feps_plumerise - computes FEPS plumrise
  - feps_timeprofile
  - feps_weather
  - hycm_std-v5.1.0-openmpi - MPI hysplit, optimized for openmpi
  - hycm_std-v5.1.0-mpich - MPI hysplit, optimized for mpich
  - hycs_std-v5.1.0 - hysplit
  - hytm_std-v5.1.0-openmpi - MPI hysplit trajectories, optimized for openmpi
  - hytm_std-v5.1.0-mpich - MPI hysplit trajectories, optimized for mpich
  - hyts_std-v5.1.0 - hysplit trajectories
  - hycm_std-v5.2.3-openmpi - MPI hysplit, optimized for openmpi
  - hycm_std-v5.2.3-mpich - MPI hysplit, optimized for mpich
  - hycs_std-v5.2.3 - hysplit
  - hytm_std-v5.2.3-openmpi - MPI hysplit trajectories, optimized for openmpi
  - hytm_std-v5.2.3-mpich - MPI hysplit trajectories, optimized for mpich
  - hyts_std-v5.2.3 - hysplit trajectories
  - hysplit2netcdf - converts hysplit concentration output to netcdf
  - makepolygons
  - profile - extracts local met information
  - bulk_profiler_csv
  - vsmkgs
  - vsmoke

All `feps_*` binaries support the  ```-h``` option to get usage information.

