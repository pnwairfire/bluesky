`bsp-output-visualizer` is a [dash](https://dash.plot.ly/) app that
generates graphs from bluesky output.

To run it, use:

    docker run --rm -ti --user bluesky \
        -p 8050:8050 \
        --name bsp-output-visualizer \
        bluesky \
        bsp-output-visualizer -p 8050

And then load http://localhost:8050/ in a web browser (e.g. Chrome or FireFox).
No output will be loaded, but you can drag and drop or select an output
json file to open.

To open the app with pre-loaded output file, mount the output directory
and use the `-i` option. For example, assuming your output files is
`$PWD/output/output.json`:

    docker run --rm -ti -p 8050:8050 --name bsp-output-visualizer \
         -v $PWD/output/:$PWD/output/ bluesky \
        bsp-output-visualizer -p 8050 -i $PWD/output/output.json

To run the app in debug mode with your local copy of the bluesky code,
use the following (assuming you're in the repo root directory):

    docker run --rm -ti --user bluesky \
        -p 8050:8050 \
        --name bsp-output-visualizer \
        -v $PWD/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        -w /bluesky/ \
        bluesky \
        ./bin/bsp-output-visualizer  -d -p 8050

To run in the background with named container and path prefix:

    docker run --rm -d --user bluesky \
        -p 8050:8050 \
        --name bsp-output-visualizer \
        bluesky \
        bsp-output-visualizer -p 8050 \
        --url-path-prefix /bluesky-output/v1/
