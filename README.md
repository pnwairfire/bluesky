# BlueSky Pipeline

BlueSky Framework rearchitected as a pipeable collection of standalone modules.

## Development

### Install Dependencies

If using the fuelbeds module, you'll need to manually install some dependencies
needed by the fccsmap package, which fuelbeds uses. See the
[fccsmap github page](https://github.com/pnwairfire/fccsmap)
for instructions.

Run the following to install python dependencies:

    pip install -r requirements.txt

Run the following for installing development dependencies (such as for running
tests):

    pip install -r dev-requirements.txt

### Setup Environment

This project contains a single package, ```bluesky```. To import bluesky
package in development, you'll have to add the repo root directory to the
search path. The ```bsp``` script does this automatically, if
necessary.

## Running tests

Use pytest:

    py.test
    py.test test/bluesky/path/to/some_tests.py

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about using pytest.

## Installation

### Installing With pip

First, install pip:

    sudo apt-get install python-pip

Then, to install, for example, v0.2.1, use the following:

    pip install git+https://github.com/pnwairfire/bluesky@v0.2.1

Or, if using the bluesky package in another project, add it to your project's
requirements.txt:

    git+ssh://git@github.org/pnwairfire/bluesky@v0.2.1

If you get an error like    ```AttributeError: 'NoneType' object has no
attribute 'skip_requirements_regex```, it means that you need in upgrade pip.
One way to do so is with the following:

    pip install --upgrade pip

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

    $ bsp fuelbeds fuelloading < /path/to/input/fires/json/file.json

#### Data Format

```bsp``` supports inputting and outputing only json formatted fire data.
If you have csv formatted fire data, you can use ```bsp-csv2json``` to convert
your data to json format.  For example, assume fires.csv contains the
following data:

    id,event_id,latitude,longitude,type,area,date_time,elevation,slope,state,county,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,consumption_flaming,consumption_smoldering,consumption_residual,consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm25,pm10,co,co2,ch4,nox,nh3,so2,voc,canopy,event_url,fccs_number,owner,sf_event_guid,sf_server,sf_stream_name,timezone,veg
    SF11C14225236095807750,SF11E826544,25.041,-77.379,RX,99.9999997516,201501200000Z,0.0,10.0,Unknown,,Unknown,-9999,2810015000,,,,,,,,,,,,10.0,12.0,12.0,22.0,130.0,150.0,,,,,6.0,6.0,6.0,6.0,40.0,80.0,13.0,30.0,4,14,7,18,5,8,,,,,,,,,,,,http://playground.dri.edu/smartfire/events/17cde405-cc3a-4555-97d2-77004435a020,,,17cde405-cc3a-4555-97d2-77004435a020,playground.dri.edu,realtime,-5.0,

running ```bsp-csv2json``` like so:

    bsp-csv2json -i fires.csv

would produce the following (written to stdout):

    {"fires": [{"slope": 10.0, "max_humid": 80.0, "co": "", "veg": "", "consumption_flaming": "", "max_temp": 30.0, "scc": 2810015000, "county": "", "fuel_1hr": "", "event_url": "http://playground.dri.edu/smartfire/events/17cde405-cc3a-4555-97d2-77004435a020", "timezone": -5.0, "owner": "", "min_temp": 13.0, "sunrise_hour": 7, "sunset_hour": 18, "rot": "", "id": "SF11C14225236095807750", "fuel_100hr": "", "fuel_10khr": "", "shrub": "", "min_wind_aloft": 6.0, "area": 99.9999997516, "event_id": "SF11E826544", "moisture_live": 130.0, "voc": "", "consumption_smoldering": "", "sf_stream_name": "realtime", "fuel_1khr": "", "min_humid": 40.0, "state": "Unknown", "rain_days": 8, "latitude": 25.041, "min_wind": 6.0, "type": "RX", "moisture_10hr": 12.0, "pm25": "", "sf_event_guid": "17cde405-cc3a-4555-97d2-77004435a020", "elevation": 0.0, "co2": "", "consumption_residual": "", "moisture_1khr": 22.0, "heat": "", "min_temp_hour": 4, "fips": -9999, "nh3": "", "max_temp_hour": 14, "max_wind_aloft": 6.0, "canopy": "", "duff": "", "date_time": "201501200000Z", "fuel_10hr": "", "moisture_duff": 150.0, "fuel_gt10khr": "", "pm10": "", "country": "Unknown", "litter": "", "longitude": -77.379, "moisture_1hr": 10.0, "so2": "", "ch4": "", "fccs_number": "", "consumption_duff": "", "nox": "", "moisture_100hr": 12.0, "grass": "", "snow_month": 5, "sf_server": "playground.dri.edu", "max_wind": 6.0}]}

You can pipe the output of ```bsp-csv2json``` directly into ```bsp```, as long
as you use the ingestions module, described below:

    bsp-csv2json -i fires.csv | bsp ingestion

Use the '-h' option to see more usage information for ```bsp-csv2json```.

#### Piping

As fire data flow through the modules within ```bsp```, the modules add to the
data without modifying what's already defined (with the exception of the
ingestion module, described below, which does modify the data).  Modules
further downstream generally work with data produced by upstream modules,
which means that order of module execution does matter.

You can run fires through a series of modules, capture the output, and
then run the output back into ```bsp``` as long as you start with a module
that doesn't depend on data updates made by any module not yet run.  For
example, assume that you start with the following fire data:

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "perimeter": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [-121.4522115, 47.4316976],
                                    [-121.3990506, 47.4316976],
                                    [-121.3990506, 47.4099293],
                                    [-121.4522115, 47.4099293],
                                    [-121.4522115, 47.4316976]
                                ]
                            ]
                        ]
                    },
                    "ecoregion": "southern"
                },
                "time": {
                    "start": "20150120T000000Z",
                    "end": "20150120T000000Z"
                }
            }
        ]
    }

Assume that this data is in a file called fires.json, and that you run
it through the fuelbeds module, with the following:

    bsp -i fires.json fuelbeds

You would get the folloing output (which is the input json with the addition
of the 'fuelbeds' array in the fire object):

    {
        "fires": [{
            "name": "Natural Fire near Snoqualmie Pass, WA",
            "event_id": "SF11E826544",
            "fuelbeds": [{
                "fccs_id": "49",
                "pct": 50.0
            }, {
                "fccs_id": "46",
                "pct": 50.0
            }],
            "location": {
                "perimeter": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [-121.4522115, 47.4316976],
                                [-121.3990506, 47.4316976],
                                [-121.3990506, 47.4099293],
                                [-121.4522115, 47.4099293],
                                [-121.4522115, 47.4316976]
                            ]
                        ]
                    ]
                },
                "ecoregion": "southern",
                "area": 2398.94477979842
            },
            "time": {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z"
            },
            "id": "SF11C14225236095807750"
        }]
    }

This output could be piped back into ```bsp``` and run through the consumption
module, like so:

    bsp -i fires.json fuelbeds | bsp consumption

yielding the following augmented output:

    {
        "fires": [{
            "name": "Natural Fire near Snoqualmie Pass, WA",
            "event_id": "SF11E826544",
            "fuelbeds": [{
                "fccs_id": "49",
                "pct": 50.0,
                "consumption": {
                    /* ...consumption output... */
                }
            }, {
                "fccs_id": "46",
                "pct": 50.0,
                "consumption": {
                    /* ...consumption output... */
                }
            }],
            "location": {
                "perimeter": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [-121.4522115, 47.4316976],
                                [-121.3990506, 47.4316976],
                                [-121.3990506, 47.4099293],
                                [-121.4522115, 47.4099293],
                                [-121.4522115, 47.4316976]
                            ]
                        ]
                    ]
                },
                "ecoregion": "southern",
                "area": 2398.94477979842
            },
            "time": {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z"
            },
            "id": "SF11C14225236095807750"
        }]
    }

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

    {
        "fires": [{
            "name": "Natural Fire near Snoqualmie Pass, WA",
            "event_id": "SF11E826544",
            "fuelbeds": [{
                "fccs_id": "49",
                "pct": 50.0,
                "consumption": {
                    /* ...consumption output... */
                },
                "emissions": {
                    /* ...emissions output... */
                }
            }, {
                "fccs_id": "46",
                "pct": 50.0,
                "consumption": {
                    /* ...consumption output... */
                },
                "emissions": {
                    /* ...emissions output... */
                }
            }],
            "location": {
                "perimeter": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [
                            [
                                [-121.4522115, 47.4316976],
                                [-121.3990506, 47.4316976],
                                [-121.3990506, 47.4099293],
                                [-121.4522115, 47.4099293],
                                [-121.4522115, 47.4316976]
                            ]
                        ]
                    ]
                },
                "ecoregion": "southern",
                "area": 2398.94477979842
            },
            "time": {
                "start": "20150120T000000Z",
                "end": "20150120T000000Z"
            },
            "id": "SF11C14225236095807750"
        }]
    }

##### Pretty-Printing JSON Output

To get indented and formated output like the above examples, try
[json.tool](https://docs.python.org/2.7/library/json.html).  It will
work only if you let the results go to STDOUT.  For example:

    bsp -i fires.json fuelbeds | python -m json.tool

#### Ingestion

The ingestion module does various things.  For each fire, it does the following:

**1. Nests the entire fire obect under key 'input.**

For example,

    {
        "fires": [
            {
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200
                }
            }
        ]
    }

would become:

    {
        "fires": [
            {
                "input": {
                    "location": {
                        "latitude": 47.4316976,
                        "longitude": -121.3990506,
                        "area": 200
                    }
                }
            }
        ]
    }

In so doing, it keeps a record of the initial data, which will remain untouched.

**2. Copies recognized fields back up to the top level**

For example,

    {
        "fires": [
            {
                "input": {
                    "location": {
                        "latitude": 47.4316976,
                        "longitude": -121.3990506,
                        "area": 200,
                        "foo": "bar"
                    }
                }
            }
        ]
    }

would become,

    {
        "fires": [
            {
                "input": {
                    "location": {
                        "latitude": 47.4316976,
                        "longitude": -121.3990506,
                        "area": 200,
                        "foo": "bar"  /*  <-- This is ignored */
                    }
                },
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200,
                }
            }
        ]
    }

In this step, it looks for nested fields both in the correctly nested
locations as well as in the root fire object.  For example:

    {
        "fires": [
            {
                "input": {
                    "location": {
                        "latitude": 47.4316976,
                        "longitude": -121.3990506
                    },
                    "area": 200
                }
            }
        ]
    }

would become,

    {
        "fires": [
            {
                "input": {
                    "location": {
                        "latitude": 47.4316976,
                        "longitude": -121.3990506
                    },
                    "area": 200
                },
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200,
                }
            }
        ]
    }

**3. Copies custom fields up to the top level**

User-identified fields that should also be copied from the input data up to
the top level can be configured.

*(Not yet implemented)*

**4. Sets defaults**

There are no hardcoded defaults, but defualts can be configured.

*(Not yet implemented)*

**5. Sets derived fields**

This entails setting undefined fields (such as 'name') from other fields'
values. For example, given the following location information

    {
        ...
        "location": {
            "latitude": 47.4316976,
            "longitude": -121.4522115
        }
        ...
    }

The name (if not set already) would be set to

    "Unnamed fire near 47.43170, -121.45221"

**6. Validates the fire data**

For example, if there is not location information, or if the nested location
is insufficient, a ```ValueError``` is raised.

##### Ingestion example

As a full example, starting with the following input data (which we'll
assume is in fires.json):

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200,
                    "foo": "bar"
                },
                "ecoregion": "southern",
                "time": {
                    "start": "20150120T000000Z",
                    "end": "20150120T000000Z"
                },
                "bar": 123
            }
        ]
    }

if you pass this data through ingestion:

    bsp -i fires.json ingestion

you'll end up with this:

    {
        "fires": [
            {
                "event_id": "SF11E826544",
                "id": "SF11C14225236095807750",
                "input": {
                    "event_id": "SF11E826544",
                    "id": "SF11C14225236095807750",
                    "location": {
                        "area": 200,
                        "ecoregion": "southern",
                        "latitude": 47.4316976,
                        "longitude": -121.3990506,
                        "foo": "bar"
                    },
                    "ecoregion": "southern",
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "time": {
                        "end": "20150120T000000Z",
                        "start": "20150120T000000Z"
                    }
                    "bar": 123
                },
                "location": {
                    "area": 200,
                    "ecoregion": "southern",
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "ecoregion": "southern"
                },
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "time": {
                    "end": "20150120T000000Z",
                    "start": "20150120T000000Z"
                }
            }
        ]
    }

Note that "foo" and "bar" were ignored (though left under 'input'), and
"ecoregion" got moved under "location".

#### Notes About Input Fire Data

##### Perimeter vs. Lat + Lng + Area

One thing to note about the fire data is that the location can be specified by
a single lat/lng pair with area (assumed to be acres) or by perimeter polygon
data. The following is an example of the former:

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "latitude": 47.123,
                    "longitude": -120.379,
                    "area": 200,
                    "ecoregion": "southern"
                },
                "time": {
                    "start": "20150120T000000Z",
                    "end": "20150120T000000Z"
                }
            }
        ]
    }

while the following is an example of the latter:

    {
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA",
                "location": {
                    "perimeter": {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [
                                [
                                    [-121.4522115, 47.4316976],
                                    [-121.3990506, 47.4316976],
                                    [-121.3990506, 47.4099293],
                                    [-121.4522115, 47.4099293],
                                    [-121.4522115, 47.4316976]
                                ]
                            ]
                        ]
                    },
                    "ecoregion": "southern"
                },
                "time": {
                    "start": "20150120T000000Z",
                    "end": "20150120T000000Z"
                }
            }
        ]
    }
