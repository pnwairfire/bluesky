# Development

First, clone the repo and install depenencies, as described in the
[installation](docs/installation.md) and
[dependencies](docs/dependencies.md) docs.

## PYTHONPATH

This project contains a single package, ```bluesky```. To import bluesky
in development, you'll have to add the repo root directory to the
search path. The ```bsp``` script does this automatically, so it's only
necessary for importing bluesky elsewhere.


## Running tests

Use pytest:

    py.test
    py.test test/bluesky/path/to/some_tests.py

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about using pytest.



## Testing export emails

requirements-dev.txt includes the maildump package, which has an smtp server
that you cah use to catch and thus test export emails.  Once you've installed
the package, you can run the server with

    python -m maildump_runner.__main__

Theoretically, you should be able to run it by simply invoking ```maildump```,
but that doesn't seem to always work within virtual environments (e.g. if you
use pyenv + virtualenv).


