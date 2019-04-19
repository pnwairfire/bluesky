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

    $ bsp -i /path/to/input/fires/json/file.json -o /path/to/output/modified/fires/json/file.json fuelbeds consumption

Example of piping in and redirecting output to file

    $ cat /path/to/input/fires/json/file.json | bsp fuelbeds > /path/to/output/modified/fires/json/file.json

Example of redirecting input from and outputing to file:

    $ bsp fuelbeds consumption emissions < /path/to/input/fires/json/file.json > /path/to/output/modified/fires/json/file.json

Example of redirecting input from file and outputing to stdout

    $ bsp fuelbeds < /path/to/input/fires/json/file.json

#### Data Format

Note that this section covers the format of the input data
(json vs csv), not the content.  For information about the
expected input fields, see the [input data doc](input-data.md)


```bsp``` supports inputting and outputing only json formatted fire data.
If you have csv formatted fire data, you can use ```bsp-csv2json``` to convert
your data to json format.  For example, assume fires.csv contains the
following data:

    id,event_id,latitude,longitude,type,area,date_time,elevation,slope,state,county,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,consumption_flaming,consumption_smoldering,consumption_residual,consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm2.5,pm10,co,co2,ch4,nox,nh3,so2,voc,canopy,event_url,fccs_number,owner,sf_event_guid,sf_server,sf_stream_name,timezone,veg
    SF11C14225236095807750,SF11E826544,25.041,-77.379,RX,99.9999997516,201501200000Z,0.0,10.0,Unknown,,Unknown,-9999,2810015000,,,,,,,,,,,,10.0,12.0,12.0,22.0,130.0,150.0,,,,,6.0,6.0,6.0,6.0,40.0,80.0,13.1,30.0,4,14,7,18,5,8,,,,,,,,,,,,http://playground.dri.edu/smartfire/events/17cde405-cc3a-4555-97d2-77004435a020,,,17cde405-cc3a-4555-97d2-77004435a020,playground.dri.edu,realtime,-5.0,

running ```bsp-csv2json``` like so:

    bsp-csv2json -i fires.csv

would produce the following (written to stdout):


    # TODO: fill in output

You can pipe the output of ```bsp-csv2json``` directly into ```bsp```, as long
as you use the ingestions module, described below:

    bsp-csv2json -i fires.csv | bsp ingestion

Use the '-h' option to see more usage information for ```bsp-csv2json```.

#### Piping

As fire data flow through the modules within ```bsp```, the modules add to the
data without modifying what's already defined (with the exception of the
ingestion, merge, and filter modules, described below, which do modify the data).
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

    bsp -i fires.json fuelbeds | bsp fuelbeds consumption

The second pass through the fuelbeds module would reinitialize the fuelbeds
array created by the first pass through the module. After running through
consumption, you would get the same output as above.  Though this re-running
of the fuelbeds module is pointless in this example, there may be situations
where you'd like to re-run your data through a module without starting from
the beginning of the pipeline.

Here's an example that runs through comsumption, captures the output, then
runs the output back through consumption and on through emissions:

    bsp -i fires.json fuelbeds consumption -o fires-c.json
    cat fires-c.json | bsp consumption emissions > fires-e.json

```fires-c.json``` would contain the output listed above.  ```fires-e.json```
would contain this output, agumented with emissions data:

    # TODO: fill in output

##### Pretty-Printing JSON Output

To get indented and formated output like the above examples, try
[json.tool](https://docs.python.org/3.5/library/json.html).  It will
work only if you let the results go to STDOUT.  For example:

    bsp -i fires.json --indent 4 fuelbeds

#### Ingestion

For each fire, the ingestion module does the following:

 1. Moves the raw fire object to the 'parsed_input' array under the ingestion module's processing record -- In so doing, it keeps a record of the initial data, which will remain untouched.
 2. Copies recognized fields back into a fire object under the 'fires' array -- In this step, it looks for nested fields both in the correctly nested
locations as well as in the root fire object.
 3. Validates the fire data -- For example, if there is no location information, or if the nested location is insufficient, a ```ValueError``` is raised.

Some proposed but not yet implemented tasks:

 1. Copy custom fields up to the top level -- i.e. user-identified fields that should also be copied from the input data up to the top level can be configured.
 2. Set defaults -- There are no hardcoded defaults, but defaults could be configured
 3. Sets derived fields -- There's no current need for this, but an example would be to derive

##### Ingestion example

###### Example 1

Assume you start with the following data:

    # TODO: fill in new example

It would become:

    # TODO: fill in output


Notice:
 - The 'raw' input under processing isn't purely raw, as the fire has been assigned an id ("ac226ee6").  This is the one auto-generated field that you will find under 'processing' > 'parsed_input'.  If the fire object already contains an id, it will be used, in which case the raw fire input is in fact exactly what the user input.
 - The 'area' and 'utc_offset' keys are initially defined at the top level, but, after ingestion, are under the 'activity' > 'location' object.  Similarly, 'name' gets moved under 'event_of' (since names apply to fire events, not to fire locations).
 - The 'event_id' key gets moved under 'event_of' and is renamed 'id'.

###### Example 2

As a fuller example, starting with the following input data (which we'll
assume is in fires.json):

    # TODO: fill in new example

if you pass this data through ingestion:

    bsp -i fires.json ingestion

you'll end up with this:

    # TODO: fill in output


Notice:
 - "foo" and "bar" were ignored (though left in the recorded raw input)
 - "ecoregion" got moved under "activity" > location"

#### Merge

TODO: fill in this section...

#### Filter

TODO: fill in this section...

#### Notes About Input Fire Data

##### GeoJSON vs. Lat + Lng + Area

One thing to note about the fire data is that the location can be specified by
a single lat/lng pair with area (assumed to be acres) or by GeoJSON
data, such as a polygon or multi-polygon representing the perimeter.
The following is an example of the former:

    # TODO: fill in new example

while the following is an example of the latter:

    # TODO: fill in new example


#### Log File

`bsp` produces log output, either to file or to stdout.  The log level
is set with the `--log-level` flag.  The log output looks like the following:

```
2019-02-22 06:24:48,191 INFO: BlueSky v4.0.6
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
2019-02-22 06:24:48,192 INFO: input file: /data/json/1-fire-24hr-20150121-Seattle-WA-post-ingestion.json
2019-02-22 06:24:48,192 INFO: indent: None
2019-02-22 06:24:48,192 DEBUG: Status logging disabled - not submitting 'Good','Main', 'Start', {}.
2019-02-22 06:24:48,192 DEBUG: Status logging disabled - not submitting 'Good','Main', 'Finish', {}.
2019-02-22 06:25:25,566 INFO: Running ingestion module
2019-02-22 06:25:25,566 DEBUG: Setting activity array in fire object
2019-02-22 06:25:25,566 DEBUG: Status logging disabled - not submitting 'Good','ingestion', 'Finish', {}.
2019-02-22 06:25:25,566 DEBUG: Status logging disabled - not submitting 'Good','Main', 'Finish', {}.
2019-02-22 06:24:48,193 INFO: Fire counts: {'fires': 1}
```



### Other Executables

the bluesky package includes these other executables:

 - bsp-csv2json - converts csv formated fire data to json format, as expcted by ```bsp```
 - feps_plumerise - computes FEPS plumrise
 - feps_weather -
 - hycm_std - MPI hysplit
 - hycs_std - hysplit
 - hysplit2netcdf - converts hysplit concentration output to netcdf
 - profile - extracts local met information
 - vsmkgs -
 - vsmoke -


`bsp-csv2json`, `feps_plumerise`, and `feps_weather` all
support the  ```-h``` option to get usage information.

