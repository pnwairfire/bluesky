# Container with all of bluesky's dependencies, to be used
# as dev environment and as base for container in which bluesky
# is to be installed.
#
# Example of how to use in dev environment, assuming you've built the
# image with tag 'bluesky-base':
#
#   docker run --name bluesky-base \
#      -v /path/to/bluesky/repo/:/bluesky/ -w /bluesky/ \
#      bluesky-base pip install --no-binary gdal \
#      --trusted-host pypi.smoke.airfire.org -r requirements.txt
#   docker commit bluesky-base bluesky-base
#   docker run -v /path/to/bluesky/repo/:/bluesky/ \
#      bluesky-base /bluesky/bin/bsp ...

FROM ubuntu:16.04

MAINTAINER Joel Dubowy

# Install base dependencies
# Note: upgrade distribute and install png and freetype libs for
#   matplotlib, which is needed by bluesky kml
RUN apt-get update \
    && apt-get install -y \
        g++ \
        gcc \
        make \
        dialog \
        less \
        python3 \
        python3-dev \
        python3-pip \
    && pip3 install --upgrade \
        pip3 \
        distribute

RUN apt-get install -y \
        libfreetype6-dev \
        libpng16-dev \
        libnetcdf-dev \
        libproj-dev \

# Install numpy and gdal
# Note: numpy 1.8.0 needs to be installed before libgdal
RUN pip3 install \
        numpy==1.8.0 \
    && apt-get install -y \
        libgdal-dev \
        gdal-bin \ # install gdal-bin for gdalwarp and gdal_translate
        nco \
    && apt-get install -y \
        python3-gdal \
    && apt-get install -y \
        libxml2-dev \
        libxslt1-dev

# mapserver and mapscript are needed to lookup ecoregion in consume
RUN apt-get install -y \
        mapserver-bin \
        python-mapscript  # NOT SURE IF THIS WILL WORK WITH PYTHON 3
