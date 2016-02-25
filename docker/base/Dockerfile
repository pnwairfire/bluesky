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

FROM ubuntu:12.04

MAINTAINER Joel Dubowy

# Install base dependencies
# Note: upgrade distribute and install png and freetype libs for
#   matplotlib, which is needed by bluesky kml
RUN apt-get update \
    && apt-get install -y \
        g++ \
        gcc \
        libfreetype6-dev \
        libpng12-dev \
        make \
        nco \
        python \
        python-dev \
        python-pip \
    && apt-get install -y \
        libnetcdf-dev \
        proj \
    && pip install --upgrade \
        pip \
        distribute

# Install numpy and gdal
# Note: numpy 1.8.0 needs to be installed before libgdal
RUN pip install \
        numpy==1.8.0 \
    && apt-get install -y \
        libgdal1-1.7.0 \
    && apt-get install -y \
        python-gdal \
    && apt-get install -y \
        libxml2-dev \
        libxslt1-dev

# install gdal-bin for gdalwarp and gdal_translate
RUN apt-get install -y \
    gdal-bin

# mapserver and mapscript are needed to lookup ecoregion in consume
RUN apt-get install -y \
     mapserver-bin \
     python-mapscript
