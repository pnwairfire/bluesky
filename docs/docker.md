## Using Docker to run BlueSky

A Dockerfile is included in this repo. It can be used to run bluesky
out of the box or as a base environment for development.

### Install and Start Docker

See https://www.docker.com/community-edition for platform specific
installation instructions.


### Build Bluesky Docker Image from Dockerfile

    cd /path/to/bluesky/repo/
    docker build -t bluesky .

### Obtain pre-built docker image

As an alternative to building the image yourself, you can use the pre-built
complete image.

    docker pull pnwairfire/bluesky

See the [bluesky docker hub page](https://hub.docker.com/r/pnwairfire/bluesky/)
for more information.


### Run Complete Container

If you run the image without a command, i.e.:

    docker run --rm bluesky

it will output the bluesky help image.  To run bluesky with piped input,
use something like the following:

    echo '{
        "fire_information": [{
            "id": "SF11C14225236095807750",
            "event_of": {
                "id": "SF11E826544",
                "name": "Natural Fire near Snoqualmie Pass, WA"
            },
            "growth": [{
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
                    "ecoregion": "southern",
                    "utc_offset": "-09:00"
                }
            }]
        }]
    }' | docker run --rm -i bluesky \
        bsp ingestion fuelbeds consumption emissions --indent 4 | less

To run bluesky with file input, you'll need to use the '-v' option to
mount host machine directories in your container.  For example, suppose
you've got the bluesky git repo in $HOME/code/pnwairfire-bluesky/, you
could run something like the following:

    docker run --rm \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        bluesky bsp \
        -i /bluesky/test/data/json/fire_locations-2015080500-fromdailycsv-4fires-4days.json \
        ingestion fuelbeds consumption emissions

### Using image for development

To use the docker image to run bluesky from your local repo, you need to
set PYTHONPATH and PATH variables in your docker run command.

For example

    docker run --rm \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:$PATH \
        bluesky bsp -h



Another example:

    docker run --rm -ti \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:$PATH \
        -w /bluesky/ \
        bluesky \
        bsp --log-level=DEBUG \
        -i ./test/data/json/1-fire-24hr-20140530-CA-post-ingestion.json \
        -o ./test/data/json/1-fire-24hr-20140530-CA-post-ingestion-output.json \
        ingestion fuelbeds consumption emissions


Another example, running `bsp` through vsmoke dispersion:

    echo '{
        "config": {
            "emissions": {
                "species": ["PM2.5"]
            },
            "dispersion": {
                "start": "2014-05-30T00:00:00",
                "num_hours": 24,
                "model": "vsmoke",
                "output_dir": "/bsp-output/bsp-dispersion-output/{run_id}"
            }
        },
        "fire_information": [
            {
                "meta":{
                    "vsmoke": {
                        "wd": 30,
                        "ws": 10
                    }
                },
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Fire Near Wolf Creek, Winthrop, WA"
                },
                "id": "SF11C14225236095807750",
                "type": "wildfire",
                "growth": [
                    {
                        "start": "2014-05-29T17:00:00",
                        "end": "2014-05-30T17:00:00",
                        "location": {
                            "area": 10000,
                            "ecoregion": "western",
                            "latitude": 48.4956218,
                            "longitude": -120.2663579,
                            "utc_offset": "-07:00"
                        }
                    }
                ]
            }
        ]
    }' | docker run --rm -i -v $HOME/docker-bsp-output:/bsp-output/ \
        bluesky bsp --indent 4 ingestion fuelbeds consumption \
        emissions timeprofiling dispersion > out.json


Another example, running `bsp` from the repo through HYSPLIT dispersion
and KML visualization:

    docker run --rm -ti \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:$PATH \
        -v $HOME/docker-bsp-output/:/bsp-output/ \
        -v $HOME/Met/CANSAC/6km/ARL/:/Met/CANSAC/6km/ARL/ \
        -w /bluesky/ \
        bluesky \
        bsp --log-level=DEBUG \
        -i ./test/data/json/1-fire-24hr-20140530-CA-post-ingestion.json \
        -o ./test/data/json/1-fire-24hr-20140530-CA-post-ingestion-output.json \
        -c ./test/config/ingestion-through-visualization/DRI6km-2014053000-24hr-PM2.5-compute-grid-km.json \
        ingestion fuelbeds consumption emissions \
        timeprofiling findmetdata localmet plumerising \
        dispersion visualization export

Another example, running through hysplit dispersion:

    echo '{
        "config": {
            "emissions": {
                "species": ["PM2.5"]
            },
            "findmetdata": {
                "met_root_dir": "/Met/CANSAC/6km/ARL/"
            },
            "dispersion": {
                "start": "2014-05-30T00:00:00",
                "num_hours": 24,
                "model": "hysplit",
                "output_dir": "/bsp-output/bsp-dispersion-output/{run_id}",
                "hysplit": {
                    "grid": {
                        "spacing": 6.0,
                        "boundary": {
                            "ne": {
                                "lat": 45.25,
                                "lng": -106.5
                            },
                            "sw": {
                                "lat": 27.75,
                                "lng": -131.5
                            }
                        }
                    }
                }
            },
            "visualization": {
                "target": "dispersion",
                "hysplit": {
                    "images_dir": "images/",
                    "data_dir": "data/"
                }
            },
            "export": {
                "modes": ["localsave"],
                "extra_exports": ["dispersion", "visualization"],
                "localsave": {
                    "dest_dir": "/bsp-output/bsp-local-exports/"
                }
            }
        },
        "fire_information": [
            {
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Yosemite, CA"
                },
                "id": "SF11C14225236095807750",
                "type": "wildfire",
                "growth": [
                    {
                        "start": "2014-05-29T17:00:00",
                        "end": "2014-05-30T17:00:00",
                        "location": {
                            "area": 10000,
                            "ecoregion": "western",
                            "latitude": 37.909644,
                            "longitude": -119.7615805,
                            "utc_offset": "-07:00"
                        }
                    }
                ]
            }
        ]
    }' | docker run --rm -i -v $HOME/docker-bsp-output/:/bsp-output/ \
        -v $HOME/Met/CANSAC/6km/ARL/:/Met/CANSAC/6km/ARL/ bluesky \
        bsp --log-level=DEBUG ingestion fuelbeds consumption emissions \
        timeprofiling findmetdata localmet plumerising dispersion \
        visualization export --indent 4 > out.json

Remember that, in the last three dispersion examples, the dispersion output
will be under `$HOME/docker-bsp-output/bsp-dispersion-output/` on your host
machine, not under `/bsp-output/bsp-dispersion-output/`. The export
directory (for the last two examples), will be under
`$HOME/bsp-local-exports`.

#### Docker wrapper script

This repo contains a script, test/scripts/run-in-docker.py, for running bsp in
the base docker container.  Use its '-h' option for usage and options.

    cd /path/to/bluesky/repo/
    ./test/scripts/run-in-docker.py -h

#### Running docker in interactive mode

Sometimes, it's useful to open a terminal within the docker container. For
example, you may want to use pdb or ipdb to debug your code.  To do so,
use the '-t' and '-i' options and run bash. The following example assumes
that your bluesky repo is in $HOME/code/pnwairfire-bluesky/, that you've got
NAM84 met data in $HOME/Met/NAM/12km/ARL/, and that you want your bsp ouput in
$HOME/docker-bsp-output/


    docker run --rm -ti \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:$PATH \
        -v $HOME/Met/NAM/12km/ARL/:/data/Met/NAM/12km/ARL/ \
        -v $HOME/docker-bsp-output/:/bsp-output/ \
        -w /bluesky/ \
        bluesky bash

Note that the above command, with the '-w /bluesky/' option, puts
you in the bluesky repo root directory. Now, you can run bsp and step into
the code as you normally would in development. E.g.:

    ./bin/bsp --log-level=DEBUG \
        -i ./test/data/json/1-fire-24hr-post-ingestion.json \
        -c ./test/config/ingestion-through-visualization/DRI6km-2014053000-24hr-PM2.5-compute-grid-km.json \
         ingestion fuelbeds consumption emissions timeprofiling findmetdata localmet \
         plumerising dispersion visualization export --indent 4 > out.json

(The './bin/' is not actually necessary in this example, since we put the
repo bin directory at the head of the PATH env var, but it doesn't hurt to
have it.)

### Notes about using Docker

#### Mounted volumes

Mounting directories outside of your home
directory seems to result in the directories appearing empty in the
docker container. Whether this is by design or not, you apparently need to
mount directories under your home directory.  Sym links don't mount either, so
you have to cp or mv directories under your home dir in order to mount them.
(This may only be an issue when using docker toolbox on Mac or Windows.)

#### Cleanup

Docker leaves behind partial images during the build process, and it leaves behind
containers after they've been used.  To clean up, you can use the following:

    # remove all stopped containers
    docker ps -a | awk 'NR > 1 {print $1}' | xargs docker rm

    # remove all untagged images:
    docker images | grep "<none>" | awk '{print $3}' | xargs docker rmi

Note: if you use the ```--rm``` option in ```docker run```, as in the
examples above, the container will be automatically deleted after use.

### Running other tools in docker

#### BlueSkyKml

Since BlueSkyKml is installed as a dependency of bluesky, you can run
```makedispersionkml``` just as you'd run ```bsp```. As with ```bsp```,
you'll need to use the '-v' option to mount host machine
directories in your container.  For example, suppose you've got bluesky
output data in /bluesky-output/20151212f/data/ and you want to create
the dispersion kml in /docker-output/, you could run something like the
following:

    docker run --rm \
        -v $HOME/bluesky-output/2015121200/data/:/input/ \
        -v $HOME/docker-output/:/output/ bluesky \
        makedispersionkml \
        -i /input/smoke_dispersion.nc \
        -l /input/fire_locations.csv \
        -e /input/fire_events.csv \
        -o /output/

#### Other tools

There are a number of other executables installed as dependencies of bluesky.
Look in ```/usr/local/bin/``` to see what's there.
