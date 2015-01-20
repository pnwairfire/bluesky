# BlueSky Pipeline

BlueSky Framework rearchitected as a pipeable collection of standalone modules.

## Development

### Install Dependencies

    pip install -r requirements.txt

### Setup Environment

To import pyairfire in development, you'll have to add the repo root directory
to the search path. Some of the scripts bin do this automatically.

## Running tests

Use nose:

    nosetests
    nosetests test/bluesky/path/to/some_tests.py
    nosetests -v -w ./test/bluesky/

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

TODO....
