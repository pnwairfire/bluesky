
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

    id,event_id,latitude,longitude,type,area,date_time,elevation,slope,state,county,country,fips,scc,fuel_1hr,fuel_10hr,fuel_100hr,fuel_1khr,fuel_10khr,fuel_gt10khr,shrub,grass,rot,duff,litter,moisture_1hr,moisture_10hr,moisture_100hr,moisture_1khr,moisture_live,moisture_duff,consumption_flaming,consumption_smoldering,consumption_residual,consumption_duff,min_wind,max_wind,min_wind_aloft,max_wind_aloft,min_humid,max_humid,min_temp,max_temp,min_temp_hour,max_temp_hour,sunrise_hour,sunset_hour,snow_month,rain_days,heat,pm2.5,pm10,co,co2,ch4,nox,nh3,so2,voc,canopy,event_url,fccs_number,owner,sf_event_guid,sf_server,sf_stream_name,timezone,veg
    SF11C14225236095807750,SF11E826544,25.041,-77.379,RX,99.9999997516,201501200000Z,0.0,10.0,Unknown,,Unknown,-9999,2810015000,,,,,,,,,,,,10.0,12.0,12.0,22.0,130.0,150.0,,,,,6.0,6.0,6.0,6.0,40.0,80.0,13.1,30.0,4,14,7,18,5,8,,,,,,,,,,,,http://playground.dri.edu/smartfire/events/17cde405-cc3a-4555-97d2-77004435a020,,,17cde405-cc3a-4555-97d2-77004435a020,playground.dri.edu,realtime,-5.0,

running ```bsp-csv2json``` like so:

    bsp-csv2json -i fires.csv

would produce the following (written to stdout):

    {"fire_information": [{"date_time": "201501200000Z", "litter": "", "county": "", "timezone": -5.0, "co": "", "elevation": 0.0, "pm10": "", "slope": 10.0, "state": "Unknown", "nh3": "", "moisture_duff": 150.0, "fuel_10khr": "", "fuel_gt10khr": "", "veg": "", "snow_month": 5, "min_temp_hour": 4, "min_wind": 6.0, "ch4": "", "moisture_1hr": 10.0, "id": "SF11C14225236095807750", "grass": "", "fuel_1hr": "", "duff": "", "max_humid": 80.0, "latitude": 25.041, "fuel_1khr": "", "heat": "", "area": 99.9999997516, "consumption_smoldering": "", "owner": "", "longitude": -77.379, "fuel_10hr": "", "rain_days": 8, "sf_server": "playground.dri.edu", "canopy": "", "min_humid": 40.0, "min_wind_aloft": 6.0, "rot": "", "fuel_100hr": "", "moisture_live": 130.0, "min_temp": 13.1, "pm2.5": "", "consumption_residual": "", "moisture_10hr": 12.0, "sunrise_hour": 7, "voc": "", "event_id": "SF11E826544", "moisture_1khr": 22.0, "so2": "", "max_wind": 6.0, "sf_event_guid": "17cde405-cc3a-4555-97d2-77004435a020", "moisture_100hr": 12.0, "event_url": "http://playground.dri.edu/smartfire/events/17cde405-cc3a-4555-97d2-77004435a020", "shrub": "", "country": "Unknown", "max_temp": 30.0, "sunset_hour": 18, "co2": "", "scc": 2810015000, "consumption_duff": "", "fccs_number": "", "nox": "", "max_temp_hour": 14, "consumption_flaming": "", "fips": -9999, "max_wind_aloft": 6.0, "type": "RX", "sf_stream_name": "realtime"}]}

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

    {
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "growth": [
                    {
                        "location": {
                            "geojson": {
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
                            "utc_offset": "-09:00"
                        },
                        "start": "2015-01-20T17:00:00",
                        "end": "2015-01-21T17:00:00"
                    }
                ]
            }
        ]
    }

Assume that this data is in a file called fires.json, and that you run
it through the fuelbeds module, with the following:

    bsp -i fires.json fuelbeds |python -m json.tool

You would get the following output (which is the input json with the addition
of the 'fuelbeds' array in the fire object, plus 'today', 'runtime', processing' and 'summary'
fields):

    {
        "summary": {
            "fuelbeds": [
                {
                    "fccs_id": "9",
                    "pct": 100.0
                }
            ]
        },
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "type": "wildfire",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "fuel_type": "natural",
                "growth": [
                    {
                        "start": "2015-01-20T17:00:00",
                        "end": "2015-01-21T17:00:00",
                        "fuelbeds": [
                            {
                                "fccs_id": "9",
                                "pct": 100.0
                            }
                        ],
                        "location": {
                            "utc_offset": "-09:00",
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4316976
                                            ],
                                            [
                                                -121.3990506,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4099293
                                            ],
                                            [
                                                -121.4522115,
                                                47.4316976
                                            ]
                                        ]
                                    ]
                                ]
                            },
                            "area": 2398.94477979842,
                            "ecoregion": "southern"
                        }
                    }
                ]
            }
        ],
        "runtime": {
            "start": "2016-09-15T18:47:13Z",
            "end": "2016-09-15T18:47:13Z",
            "modules": [
                {
                    "start": "2016-09-15T18:47:13Z",
                    "end": "2016-09-15T18:47:13Z",
                    "module_name": "fuelbeds",
                    "total": "0.0h 0.0m 0s"
                }
            ],
            "total": "0.0h 0.0m 0s"
        },
        "today": "2016-09-15",
        "config": {},
        "processing": [
            {
                "version": "0.1.0",
                "fccsmap_version": "1.0.1",
                "module_name": "fuelbeds",
                "module": "bluesky.modules.fuelbeds"
            }
        ]
    }


This output could be piped back into ```bsp``` and run through the consumption
module, like so:

    bsp -i fires.json fuelbeds | bsp consumption

yielding the following augmented output:

    {
        "processing": [
            {
                "module": "bluesky.modules.fuelbeds",
                "fccsmap_version": "1.0.1",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            },
            {
                "module": "bluesky.modules.consumption",
                "module_name": "consumption",
                "consume_version": "4.1.2",
                "version": "0.1.0"
            }
        ],
        "fire_information": [
            {
                "growth": [
                    {
                        "fuelbeds": [
                            {
                                "fccs_id": "9",
                                "consumption": {
                                    /* ...consumption output... */
                                },
                                "pct": 100.0,
                                "heat": {
                                    /* ...heat output... */
                                },
                                "fuel_loadings": {
                                    /* ...consumption output... */
                                }
                            }
                        ],
                        "heat": {
                            "summary": {
                                "flaming": 344476309730.7089,
                                "smoldering": 247784445451.14124,
                                "residual": 331813158338.9564,
                                "total": 924073913520.8065
                            }
                        },
                        "consumption": {
                            "summary": {
                                "flaming": 21529.769358169302,
                                "smoldering": 15486.527840696328,
                                "residual": 20738.322396184776,
                                "total": 57754.61959505042
                            }
                        },
                        "end": "2015-01-21T17:00:00",
                        "location": {
                            "utc_offset": "-09:00",
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [-121.4522115,47.4316976],
                                            [-121.3990506,47.4316976],
                                            [-121.3990506,47.4099293],
                                            [-121.4522115,47.4099293],
                                            [-121.4522115,47.4316976]
                                        ]
                                    ]
                                ]
                            },
                            "area": 2398.94477979842,
                            "ecoregion": "southern"
                        },
                        "start": "2015-01-20T17:00:00"
                    }
                ],
                "heat": {
                    "summary": {
                        "flaming": 344476309730.7089,
                        "smoldering": 247784445451.14124,
                        "residual": 331813158338.9564,
                        "total": 924073913520.8065
                    }
                },
                "fuel_type": "natural",
                "consumption": {
                    "summary": {
                        "flaming": 21529.769358169302,
                        "smoldering": 15486.527840696328,
                        "residual": 20738.322396184776,
                        "total": 57754.61959505042
                    }
                },
                "id": "SF11C14225236095807750",
                "type": "wildfire",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                }
            }
        ],
        "config": {},
        "today": "2016-09-15",
        "summary": {
            "consumption": {
                /* ...consumption summary... */
            },
            "fuelbeds": [
                {
                    "fccs_id": "9",
                    "pct": 100.0
                }
            ],
            "heat": {
                /* ...heat summary... */
            }
        },
        "runtime": {
            "end": "2016-09-15T18:48:22Z",
            "start": "2016-09-15T18:48:22Z",
            "modules": [
                {
                    "end": "2016-09-15T18:48:22Z",
                    "module_name": "fuelbeds",
                    "start": "2016-09-15T18:48:22Z",
                    "total": "0.0h 0.0m 0s"
                },
                {
                    "end": "2016-09-15T18:48:22Z",
                    "module_name": "consumption",
                    "start": "2016-09-15T18:48:22Z",
                    "total": "0.0h 0.0m 0s"
                }
            ],
            "total": "0.0h 0.0m 0s"
        }
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
        "processing": [
            {
                "fccsmap_version": "1.0.1",
                "module": "bluesky.modules.fuelbeds",
                "module_name": "fuelbeds",
                "version": "0.1.0"
            },
            {
                "module": "bluesky.modules.consumption",
                "module_name": "consumption",
                "version": "0.1.0",
                "consume_version": "4.1.2"
            },
            {
                "emitcalc_version": "1.0.1",
                "module": "bluesky.modules.emissions",
                "eflookup_version": "1.0.2",
                "ef_set": "feps",
                "module_name": "emissions",
                "version": "0.1.0"
            }
        ],
        "runtime": {
            "total": "0.0h 0.0m 0s",
            "end": "2016-09-15T18:52:10Z",
            "start": "2016-09-15T18:52:10Z",
            "modules": [
                {
                    "total": "0.0h 0.0m 0s",
                    "end": "2016-09-15T18:52:10Z",
                    "module_name": "fuelbeds",
                    "start": "2016-09-15T18:52:10Z"
                },
                {
                    "total": "0.0h 0.0m 0s",
                    "end": "2016-09-15T18:52:10Z",
                    "module_name": "consumption",
                    "start": "2016-09-15T18:52:10Z"
                },
                {
                    "total": "0.0h 0.0m 0s",
                    "end": "2016-09-15T18:52:10Z",
                    "module_name": "emissions",
                    "start": "2016-09-15T18:52:10Z"
                }
            ]
        },
        "config": {},
        "fire_information": [
            {
                "fuel_type": "natural",
                "emissions": {
                    "summary": {
                        "total": 99674.47838833416,
                        "CH4": 439.71054108574947,
                        "NOx": 84.99420586185778,
                        "PM2.5": 759.2284300672792,
                        "CO": 9157.402971690011,
                        "PM10": 895.8895474793892,
                        "SO2": 56.59952720314939,
                        "VOC": 2149.357747802895,
                        "NH3": 149.52053897759265,
                        "CO2": 85981.77487816624
                    }
                },
                "heat": {
                    "summary": {
                        "total": 924073913520.8066,
                        "smoldering": 247784445451.14124,
                        "flaming": 344476309730.7089,
                        "residual": 331813158338.9564
                    }
                },
                "type": "wildfire",
                "growth": [
                    {
                        "fuelbeds": [
                            {
                                "pct": 100.0,
                                "fccs_id": "9",
                                "heat": {
                                    /* ...heat output... */
                                },
                                "emissions": {
                                    /* ...emissions output... */
                                },
                                "fuel_loadings": {
                                    /* ...fuel loadings... */
                                },
                                "consumption": {
                                    /* ...consumption output... */
                                }
                            }
                        ],
                        "heat": {
                            "summary": {
                                "total": 924073913520.8066,
                                "smoldering": 247784445451.14124,
                                "flaming": 344476309730.7089,
                                "residual": 331813158338.9564
                            }
                        },
                        "emissions": {
                            "summary": {
                                "total": 99674.47838833416,
                                "CH4": 439.71054108574947,
                                "NOx": 84.99420586185778,
                                "PM2.5": 759.2284300672792,
                                "CO": 9157.402971690011,
                                "PM10": 895.8895474793892,
                                "SO2": 56.59952720314939,
                                "VOC": 2149.357747802895,
                                "NH3": 149.52053897759265,
                                "CO2": 85981.77487816624
                            }
                        },
                        "location": {
                            "ecoregion": "southern",
                            "area": 2398.94477979842,
                            "geojson": {
                                "type": "MultiPolygon",
                                "coordinates": [
                                    [
                                        [
                                            [-121.4522115,47.4316976],
                                            [-121.3990506,47.4316976],
                                            [-121.3990506,47.4099293],
                                            [-121.4522115,47.4099293],
                                            [-121.4522115,47.4316976]
                                        ]
                                    ]
                                ]
                            },
                            "utc_offset": "-09:00"
                        },
                        "end": "2015-01-21T17:00:00",
                        "start": "2015-01-20T17:00:00",
                        "consumption": {
                            "summary": {
                                "total": 57754.619595050404,
                                "smoldering": 15486.527840696328,
                                "flaming": 21529.76935816931,
                                "residual": 20738.322396184776
                            }
                        }
                    }
                ],
                "consumption": {
                    "summary": {
                        "total": 57754.619595050404,
                        "smoldering": 15486.527840696328,
                        "flaming": 21529.76935816931,
                        "residual": 20738.322396184776
                    }
                },
                "event_of": {
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "id": "SF11C14225236095807750"
            }
        ],
        "today": "2016-09-15",
        "summary": {
            "heat": {
                /* ...heat summary... */
            },
            "fuelbeds": [
                {
                    "pct": 100.0,
                    "fccs_id": "9"
                }
            ],
            "consumption": {
                /* ...consumption summary... */
            },
            "emissions": {
                /* ...emissions summary... */
            }
        }
    }

##### Pretty-Printing JSON Output

To get indented and formated output like the above examples, try
[json.tool](https://docs.python.org/3.5/library/json.html).  It will
work only if you let the results go to STDOUT.  For example:

    bsp -i fires.json fuelbeds | python -m json.tool

#### Ingestion

For each fire, the ingestion module does the following:

 1. Moves the raw fire object to the 'parsed_input' array under the ingestion module's processing record -- In so doing, it keeps a record of the initial data, which will remain untouched.
 2. Copies recognized fields back into a fire object under the 'fire_information' array -- In this step, it looks for nested fields both in the correctly nested
locations as well as in the root fire object.
 3. Validates the fire data -- For example, if there is no location information, or if the nested location is insufficient, a ```ValueError``` is raised.

Some proposed but not yet implemented tasks:

 1. Copy custom fields up to the top level -- i.e. user-identified fields that should also be copied from the input data up to the top level can be configured.
 2. Set defaults -- There are no hardcoded defaults, but defaults could be configured
 3. Sets derived fields -- There's no current need for this, but an example would be to derive

##### Ingestion example

###### Example 1

Assume you start with the following data:

    {
        "fire_information": [
            {
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506
                },
                "area": 200,
                "utc_offset": "-09:00",
                "name": "event name",
                "event_id": "jfkhfdskj"
            }
        ]
    }

It would become:

    {
        "config": {},
        "runtime": {
            "start": "2016-09-15T18:55:48Z",
            "end": "2016-09-15T18:55:48Z",
            "total": "0.0h 0.0m 0s",
            "modules": [
                {
                    "start": "2016-09-15T18:55:48Z",
                    "total": "0.0h 0.0m 0s",
                    "module_name": "ingestion",
                    "end": "2016-09-15T18:55:48Z"
                }
            ]
        },
        "today": "2016-09-15",
        "fire_information": [
            {
                "type": "wildfire",
                "fuel_type": "natural",
                "id": "03d58ba6",
                "event_of": {
                    "id": "jfkhfdskj",
                    "name": "event name"
                },
                "growth": [
                    {
                        "location": {
                            "area": 200,
                            "longitude": -121.3990506,
                            "utc_offset": "-09:00",
                            "latitude": 47.4316976
                        }
                    }
                ]
            }
        ],
        "processing": [
            {
                "version": "0.1.0",
                "parsed_input": [
                    {
                        "area": 200,
                        "type": "wildfire",
                        "utc_offset": "-09:00",
                        "name": "event name",
                        "location": {
                            "longitude": -121.3990506,
                            "latitude": 47.4316976
                        },
                        "event_id": "jfkhfdskj",
                        "id": "03d58ba6",
                        "fuel_type": "natural"
                    }
                ],
                "module_name": "ingestion",
                "module": "bluesky.modules.ingestion"
            }
        ]
    }


Notice:
 - The 'raw' input under processing isn't purely raw, as the fire has been assigned an id ("ac226ee6").  This is the one auto-generated field that you will find under 'processing' > 'parsed_input'.  If the fire object already contains an id, it will be used, in which case the raw fire input is in fact exactly what the user input.
 - The 'area' and 'utc_offset' keys are initially defined at the top level, but, after ingestion, are under the 'growth' > 'location' object.  Similarly, 'name' gets moved under 'event_of' (since names apply to fire events, not to fire locations).
 - The 'event_id' key gets moved under 'event_of' and is renamed 'id'.

###### Example 2

As a fuller example, starting with the following input data (which we'll
assume is in fires.json):

    {
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "location": {
                    "latitude": 47.4316976,
                    "longitude": -121.3990506,
                    "area": 200,
                    "utc_offset": "-09:00",
                    "foo": "bar"
                },
                "ecoregion": "southern",
                "growth": [
                    {
                        "start": "2015-01-20T17:00:00",
                        "end": "2015-01-21T17:00:00"
                    }
                ],
                "bar": 123
            }
        ]
    }

if you pass this data through ingestion:

    bsp -i fires.json ingestion

you'll end up with this:

    {
        "config": {},
        "today": "2016-09-15",
        "processing": [
            {
                "parsed_input": [
                    {
                        "bar": 123,
                        "growth": [
                            {
                                "end": "2015-01-21T17:00:00",
                                "start": "2015-01-20T17:00:00"
                            }
                        ],
                        "id": "SF11C14225236095807750",
                        "fuel_type": "natural",
                        "event_of": {
                            "name": "Natural Fire near Snoqualmie Pass, WA",
                            "id": "SF11E826544"
                        },
                        "ecoregion": "southern",
                        "type": "wildfire",
                        "location": {
                            "area": 200,
                            "foo": "bar",
                            "longitude": -121.3990506,
                            "utc_offset": "-09:00",
                            "latitude": 47.4316976
                        }
                    }
                ],
                "version": "0.1.0",
                "module": "bluesky.modules.ingestion",
                "module_name": "ingestion"
            }
        ],
        "fire_information": [
            {
                "growth": [
                    {
                        "end": "2015-01-21T17:00:00",
                        "location": {
                            "area": 200.0,
                            "ecoregion": "southern",
                            "longitude": -121.3990506,
                            "utc_offset": "-09:00",
                            "latitude": 47.4316976
                        },
                        "start": "2015-01-20T17:00:00"
                    }
                ],
                "fuel_type": "natural",
                "id": "SF11C14225236095807750",
                "event_of": {
                    "name": "Natural Fire near Snoqualmie Pass, WA",
                    "id": "SF11E826544"
                },
                "type": "wildfire"
            }
        ],
        "runtime": {
            "end": "2016-09-15T18:56:21Z",
            "total": "0.0h 0.0m 0s",
            "modules": [
                {
                    "end": "2016-09-15T18:56:21Z",
                    "total": "0.0h 0.0m 0s",
                    "start": "2016-09-15T18:56:21Z",
                    "module_name": "ingestion"
                }
            ],
            "start": "2016-09-15T18:56:21Z"
        }
    }


Notice:
 - "foo" and "bar" were ignored (though left in the recorded raw input)
 - "ecoregion" got moved under "growth" > location"

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

    {
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "growth": [
                    {
                        "start": "2015-01-20T17:00:00",
                        "end": "2015-01-21T17:00:00",
                        "location": {
                            "latitude": 47.123,
                            "longitude": -120.379,
                            "area": 200,
                            "ecoregion": "southern"
                        }
                    }
                ]
            }
        ]
    }

while the following is an example of the latter:

    {
        "fire_information": [
            {
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "growth": [
                    {
                        "start": "2015-01-20T17:00:00",
                        "end": "2015-01-21T17:00:00",
                        "location": {
                            "geojson": {
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
                        }
                    }
                ]
            }
        ]
    }

### Other Executables

the bluesky package includes three other executables:

 - bsp-arlindexer - indexes available arl met data
 - bsp-arlprofiler - extracts local met data from an arl met data file for a specific location
 - bsp-csv2json - converts csv formated fire data to json format, as expcted by ```bsp```

For usage and examples, use the ```-h``` with each script.

