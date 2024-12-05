# Installation


## Pulling Pre-built Docker Image From hub.docker.com

### Install and Start Docker

See https://www.docker.com/community-edition for platform specific
installation instructions.

### Pull image

You can pull a pre-built docker image from docker hub:

    docker pull pnwairfire/bluesky:v4.6.9

See the
[bluesky docker hub page](https://hub.docker.com/r/pnwairfire/bluesky/)
for more information.

### Add user

If you use the image as is, all files created on mounted host volumes
will be owned by root.  To add a user to the image with same group
and user ids as your host machine user, you can use the following
script included in this repo:

    ./dev/scripts/docker/add-user-to-bluesky-image \
        -i pnwairfire/bluesky:v4.6.9 -n bluesky2

Then, run bluesky with that user:

    docker run -u bluesky2 bsp -h

Any files created on mounted volumes will be owned by your user.





## Building Docker Image

A Dockerfile is included in this repo to build a bluesky image yourself.

### Install and Start Docker

See above.

### Build Bluesky Docker Image from Dockerfile

    cd /path/to/bluesky/repo/
    docker build  -t bluesky . \
        --build-arg UID=$(id -u) \
        --build-arg GID=$(id -g)

Note that the build args are so that files saved in mounted host volumes
are saved as your user.





## Installing with pip

First, install pip3 (with sudo if necessary):

    apt-get install python3-pip
    pip3 install --upgrade pip

Then, to install, for example, v4.6.9, use the following (with sudo if necessary):

    pip3 install --no-binary gdal --extra-index https://pypi.airfire.org/simple bluesky==4.6.9

Or, if using the bluesky package in another project, add it to your project's
requirements.txt:

    --extra-index https://pypi.airfire.org/simple/
    bluesky==4.6.9

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
    pip3 install -c constraints.txt --no-binary gdal -r requirements.txt

Run the following to install packages required for development and testing:

    pip3 install -c constraints.txt -r requirements-test.txt
    pip3 install -c constraints.txt -r requirements-dev.txt





## Notes

### pip issues

If you get an error like    ```AttributeError: 'NoneType' object has no
attribute 'skip_requirements_regex```, it means you need in upgrade
pip. One way to do so is with the following:

    pip3 install --upgrade pip

### gdal issues

If, when you use fccsmap, you get the following error:

    *** Error: No module named _gdal_array

it's because your osgeo package (/path/to/site-packages/osgeo/) is
missing _gdal_array.so.  This happens when gdal is built on a
machine that lacks numpy.  The ```--no-binary :all:``` in the pip
install command, above, is meant to fix this issue.  If it doesn't work,
try uninstalling the gdal package and then re-installing it individually
with the ```--no-binary``` option to pip:

    pip3 uninstall -y GDAL
    pip3 install --no-binary :all: gdal==1.11.2

If this doesn't work, uninstall gdal, and then install it manually:

    pip3 uninstall -y GDAL
    wget https://pypi.python.org/packages/source/G/GDAL/GDAL-1.11.2.tar.gz
    tar xzf GDAL-1.11.2.tar.gz
    cd GDAL-1.11.2
    python setup.py install

