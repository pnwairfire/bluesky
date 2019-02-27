# Development

First, clone the repo and build the docker image,
as described in the [installation](installation.md).  (If opting
to develop without docker, see also the
[dependencies](dependencies.md) docs.  The instrucitons on this
page, however, assume that you use docker.)

## PYTHONPATH

This project contains a single package, ```bluesky```. To import bluesky
in development, you'll have to add the repo root directory to the
search path. The ```bsp``` script does this automatically, so it's only
necessary for importing bluesky elsewhere.


## Interactive python session

The following starts an ipython session with docker with your local
copy of the code mounted in the docker container and added
to the beggining of PATH and PYTHONPATH env vars.

    docker run --rm -ti \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ -e PATH=/bluesky/bin/:$PATH \
        bluesky ipython



## Running tests

The following uses py.test to run unit and regression tests
within docker with your local
copy of the code mounted in the docker container and added
to the beggining of PATH and PYTHONPATH env vars.

    docker run --rm -ti \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ -e PATH=/bluesky/bin/:$PATH \
        bluesky py.test

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about using pytest.



## Testing export emails

For testing export emails, you can use maildump package, which has
an smtp server that you cah use to catch and thus test export emails.
Once you've installed the package, you can run the server with

    pip3 install maildump
    python -m maildump_runner.__main__

Theoretically, you should be able to run it by simply invoking ```maildump```,
but that doesn't seem to always work within virtual environments (e.g. if you
use pyenv + virtualenv).
