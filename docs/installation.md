# Installation




## Installing with Docker

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




## Installing with pip

First, install pip (with sudo if necessary):

    apt-get install python-pip
    pip install --upgrade pip

Then, to install, for example, v4.0.6, use the following (with sudo if necessary):

    pip install --no-binary gdal --extra-index https://pypi.airfire.org/simple bluesky==4.0.6

Or, if using the bluesky package in another project, add it to your project's
requirements.txt:

    --extra-index https://pypi.airfire.org/simple/
    bluesky==4.0.6

See the Notes section, below, for information on resolving pip and
gdal issues.




## Cloning the Repo

This is mostly for development.

Via ssh:

    git clone git@github.com:pnwairfire/bluesky.git pnwairfire-bluesky

or http:

    git clone https://github.com/pnwairfire/bluesky.git pnwairfire-bluesky

### Install python Dependencies


Run the following to install python dependencies:

    cd pnwairfire-bluesky
    pip install --no-binary gdal -r requirements.txt

Run the following to install packages required for development and testing:

    pip install -r requirements-test.txt
    pip install -r requirements-dev.txt





## Notes

### pip issues

If you get an error like    ```AttributeError: 'NoneType' object has no
attribute 'skip_requirements_regex```, it means you need in upgrade
pip. One way to do so is with the following:

    pip install --upgrade pip

### gdal issues

If, when you use fccsmap, you get the following error:

    *** Error: No module named _gdal_array

it's because your osgeo package (/path/to/site-packages/osgeo/) is
missing _gdal_array.so.  This happens when gdal is built on a
machine that lacks numpy.  The ```--no-binary :all:``` in the pip
install command, above, is meant to fix this issue.  If it doesn't work,
try uninstalling the gdal package and then re-installing it individually
with the ```--no-binary``` option to pip:

    pip uninstall -y GDAL
    pip install --no-binary :all: gdal==1.11.2

If this doesn't work, uninstall gdal, and then install it manually:

    pip uninstall -y GDAL
    wget https://pypi.python.org/packages/source/G/GDAL/GDAL-1.11.2.tar.gz
    tar xzf GDAL-1.11.2.tar.gz
    cd GDAL-1.11.2
    python setup.py install

