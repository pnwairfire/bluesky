# Development

First, clone the repo and build the docker image,
as described in the [installation](installation.md).  (If opting
to develop without docker, see also the
[dependencies](dependencies.md) docs.  The instructions on this
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

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        bluesky ipython



## Running tests

The following uses py.test to run unit and regression tests
within docker with your local
copy of the code mounted in the docker container and added
to the beggining of PATH and PYTHONPATH env vars.

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        bluesky py.test --disable-pytest-warnings

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about using pytest.


## Testing export emails

For testing export emails, you can use something like the
[mailtrip](https://pypi.org/project/mailtrap/) package, which has
an smtp server that you cah use to catch and thus test export emails.


## Publishing new version

    ./dev/scripts/bump-version
    git push && git push --tags


## Profiling

To see how much time is being spent in each function call, you can
profile a run by using `bsp`'s `--profile-output-file` option.

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        bluesky bsp --profile-output-file ...


## How to debug tests in VSCode

In VSCode, open the bluesky folder, click on the Debug icon (left side), and
add "python debugger, remote attach". This will generate a `launch.json` that looks similar to the following after adding `port` and `justMyCode` settings.

    {
        // Use IntelliSense to learn about possible attributes.
        // Hover to view descriptions of existing attributes.
        // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python Debugger: Remote Attach",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost",
                    "port": 5678
                },
                "pathMappings": [
                    {
                        "localRoot": "${workspaceFolder}",
                        "remoteRoot": "."
                    }
                ],
                "justMyCode": false
            }
        ]
    }

Add breakpoints to the unit tests or other code in VSCode. Use this command to
run docker with port 5678 exposed, and pause until the debugger is connected.
Change "$HOME/code/pnwairfire-bluesky/" to match where your source code is
located on your local machine

    docker run --rm -ti --user bluesky \
        -v $HOME/code/pnwairfire-bluesky/:/bluesky/ \
        -p 5678:5678 \
        -e PYTHONPATH=/bluesky/ \
        -e PATH=/bluesky/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        bluesky python3 -m debugpy --wait-for-client --listen 0.0.0.0:5678 -m pytest --disable-pytest-warnings

In VSCode, click the debug icon, then click the green triangle to "run and debug".
The tests will start running and the output will be displayed in the debug console of
VSCode. The breakpoints should work.
