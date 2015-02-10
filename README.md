# BlueSky Pipeline

BlueSky Framework rearchitected as a pipeable collection of standalone modules.

## Development

### Install Dependencies

Run the following to install dependencies:

    pip install -r requirements.txt

Run the following for installing development dependencies (like running tests):

    pip install -r dev-requirements.txt

### Setup Environment

To import pyairfire in development, you'll have to add the repo root directory
to the search path. Some of the scripts bin do this automatically.

## Running tests

Use pytest:

    py.test
    py.test test/bluesky/path/to/some_tests.py

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about

## Installation

The repo is currently private. So, you need to be on the FERA bitbucket team
to install from the repo.

### Installing With pip

First, install pip:

    sudo apt-get install python-pip

Then, to install, for example, v4.0.0, use the following:

    sudo pip install git+ssh://git@bitbucket.org/fera/airfire-bluesky-pipeline@v4.0.0

Or add it to your project's requirements.txt:

    git+ssh://git@bitbucket.org/fera/airfire-bluesky-pipeline@v4.0.0

If you get an error like    ```AttributeError: 'NoneType' object has no attribute 'skip_requirements_regex```, it means you need in upgrade pip.  One way to do so is with the following:

    pip install --upgrade pip

## Usage:

### bsp

bsp is the main BlueSky executable.  It can be used for any combination of
the following:

 - to translate CSV-formatted fire data to JSON, and vice versa
 - to filter a set of fires by country code
 - run BlueSky fires

#### Getting Help

Use the ```-h``` flag for help:

    $ ./bin/bsp -h
    Usage: bsp [options] <module> [<module> ...]

    Options:
      -h, --help            show this help message and exit
      -l, --list-modules    lists modules available to use in pipeline; order
                            matters
      ...

Use the ```-l``` flag to see available BlueSky modules:

    $ ./bin/bsp -l

    Available Modules:

            fuelbeds
            fuelloading
            ...

#### Input / Output

The ```bsp``` executable inputs fire json data, and exports a modified version
of that fire json data.  You can input from stdin (via piping or redirecting)
or from file.  Likewise, you can output to stdout or to file.

Example of reading from and writing to file:

    $ ./bsp -i /path/to/input/fires/json/file.json -o /path/to/output/modified/fires/json/file.json fuelbeds fuelloading

Example of piping in and redirecting output to file

    $ cat /path/to/input/fires/json/file.json | ./bsp > /path/to/output/modified/fires/json/file.json fuelbeds fuelloading

Example of redirecting input from and output to file:

    $ ./bin/bsp fuelbeds fuelloading < /path/to/input/fires/json/file.json > /path/to/output/modified/fires/json/file.json

Example of redirecting input from file and outputing to stdout

    $ ./bin/bsp fuelbeds fuelloading < /path/to/input/fires/json/file.json

```bsp``` supports inputting and outputing both json and csv formatted fire data.
(The default expected format is JSON.) The following example reads in CSV fire
data from file, filters out all but USA filures, and outputs JSON formated data
to stdout

    $ ./bin/bsp -i /path/to/input/fires/csv/file.csv --input-format=CSV

...More examples...
