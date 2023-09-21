## Using Docker to run BlueSky


### Run Complete Container

If you run the image without a command, i.e.:

    docker run --rm bluesky

it will output the bluesky help image.  To run bluesky with piped input,
use something like the following:

    echo '{
        "fires": [
            {
                "id": "SF11C14225236095807750",
                "event_of": {
                    "id": "SF11E826544",
                    "name": "Natural Fire near Snoqualmie Pass, WA"
                },
                "activity": [
                    {
                        "active_areas": [
                            {
                                "start": "2015-01-20T17:00:00",
                                "end": "2015-01-21T17:00:00",
                                "ecoregion": "southern",
                                "utc_offset": "-09:00",
                                "perimeter": {
                                    "geometry": {
                                        "type": "Polygon",
                                        "coordinates": [
                                            [
                                                [-121.4522115, 47.4316976],
                                                [-121.3990506, 47.4316976],
                                                [-121.3990506, 47.4099293],
                                                [-121.4522115, 47.4099293],
                                                [-121.4522115, 47.4316976]
                                            ]
                                        ]
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }' | docker run --rm -i bluesky \
        bsp fuelbeds ecoregion consumption emissions --indent 4 | less

To run bluesky with file input, you'll need to use the '-v' option to
mount host machine directories in your container.  For example, suppose
you've got the bluesky git repo in $HOME/code/pnwairfire-bluesky/, you
could run something like the following:

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        bluesky bsp \
        -i /bluesky/dev/data/json/2-fires-24hr-20140530-CA.json \
        fuelbeds ecoregion consumption emissions

### Using image for development

To use the docker image to run bluesky from your local repo, you need to
set PYTHONPATH and PATH variables in your docker run command.

For example, to just print the helpstring:

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        bluesky bsp -h

Another example, running through emissions:

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -w /bluesky/ \
        bluesky \
        bsp --log-level=DEBUG --indent 4 \
        -i ./dev/data/json/2-fires-24hr-20140530-CA.json \
        -o ./output/{run_id}.json \
        fuelbeds ecoregion consumption emissions


Another example, running through vsmoke dispersion:

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -w /bluesky/ \
        bluesky \
        bsp --log-level=DEBUG --indent 4 \
        --run-id vsmoke-1-fire-72-hr-{timestamp:%Y%m%dT%H%M%S} \
        -i ./dev/data/json/1-fire-72hr-20140530-CA.json \
        -o ./output/{run_id}.json \
        -c ./dev/config/dispersion/dispersion-vsmoke-72hr.json \
        fuelbeds ecoregion consumption emissions timeprofile dispersion


Two more examples, running `bsp` from the repo through HYSPLIT dispersion
and KML visualization:

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -v $HOME/Met/CANSAC/4km/ARL/:/data/Met/CANSAC/4km/ARL/ \
        -w /bluesky/ \
        bluesky \
        bsp --log-level=DEBUG --indent 4 \
        --run-id hysplit-{timestamp:%Y%m%dT%H%M%S} \
        -i ./dev/data/json/1-fire-24hr-20190610-CA.json \
        -o ./output/{run_id}.json \
        -c ./dev/config/fuelbeds-through-visualization/DRI4km-2019061012-48hr-PM2.5-grid-latlng.json \
        fuelbeds ecoregion consumption emissions \
        timeprofile findmetdata localmet plumerise \
        dispersion visualization

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -v $HOME/Met/PNW/4km/ARL/:/data/Met/PNW/4km/ARL/ \
        -w /bluesky/ \
        bluesky \
        bsp --log-level=DEBUG --indent 4 \
        --run-id 2-fires-24hr-2019-07-26-WA-{timestamp:%Y%m%dT%H%M%S} \
        -i dev/data/json/2-fires-24hr-2019-07-26-WA.json \
        -o ./output/{run_id}.json \
        -c ./dev/config/fuelbeds-through-visualization/PNW4km-2019072600-24hr-PM2.5.json \
        fuelbeds ecoregion consumption emissions \
        timeprofile findmetdata localmet plumerise \
        dispersion visualization


Remember that, in the last dispersion example, the dispersion output
will be under `$HOME/code/pnwairfire-bluesky/output/dispersion-output/bsp-dispersion-output/`
on your host machine, not under `/bluesky/output/output/`.
The export directory will be under
`$HOME/code/pnwairfire-bluesky/output/exports/`.

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


    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -v $HOME/Met/NAM/12km/ARL/:/data/Met/NAM/12km/ARL/ \
        -w /bluesky/ \
        bluesky bash

Note that the above command, with the '-w /bluesky/' option, puts
you in the bluesky repo root directory. Now, you can run bsp and step into
the code as you normally would in development. E.g.:

    ./bin/bsp --log-level=DEBUG \
        -i ./dev/data/json/2-fires-24hr-20140530-CA.json \
        -c ./dev/config/fuelbeds-through-visualization/DRI6km-2014053000-24hr-PM2.5-compute-grid-km.json \
        fuelbeds ecoregion consumption emissions timeprofile \
        findmetdata localmet plumerise dispersion \
        visualization export --indent 4 > out.json

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

Docker leaves behind partial images during the build process, and it
leaves behind containers after they've been used (if you don't use the
`--rm` option, see below).  To clean up, you can use the following:

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
output data in $HOME/bluesky-output/20151212f/data/ and you want to create
the dispersion kml in $HOME/bluesky-kml-output/, you could run something
like the following:

    docker run --rm \
        -v $HOME/bluesky-output/2015121200/data/:/input/ \
        -v $HOME/bluesky-kml-output/:/output/ bluesky \
        makedispersionkml \
        -i /input/smoke_dispersion.nc \
        -l /input/fire_locations.csv \
        -e /input/fire_events.csv \
        -o /output/

#### BlueSky Output Visualizer

See [the output visualizer doc](docs/output-visualizer.md)

#### Other tools

There are a number of other executables installed as dependencies of bluesky.
Look in ```/usr/local/bin/``` to see what's there.
