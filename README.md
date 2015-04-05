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

Then, to install, for example, v0.1.5, use the following:

    pip install git+https://github.com/pnwairfire/bluesky@v0.1.5

Or, if using the bluesky package in another project, add it to your project's
requirements.txt:

    git+ssh://git@github.org/pnwairfire/bluesky@v0.1.5

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
