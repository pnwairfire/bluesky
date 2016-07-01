# Container with all of bluesky's dependencies, to be used
# as dev environment and as base for container in which bluesky
# is to be installed.
#
# Example of how to use in dev environment, assuming you've built the
# image with tag 'bluesky-base':
#
#   docker run --name bluesky-base \
#      -v /path/to/bluesky/repo/:/bluesky/ -w /bluesky/ \
#      bluesky-base pip3 install --no-binary gdal \
#      --trusted-host pypi.smoke.airfire.org -r requirements.txt
#   docker commit bluesky-base bluesky-base
#   docker run -v /path/to/bluesky/repo/:/bluesky/ \
#      bluesky-base /bluesky/bin/bsp ...

FROM ubuntu:16.04

MAINTAINER Joel Dubowy

# Install base dependencies
RUN apt-get update \
    && apt-get install -y \
        g++ \
        gcc \
        make \
        dialog \
        less \
        python3 \
        python3-dev \
        python3-pip

# upgrade distribute
RUN pip3 install --upgrade \
        distribute

# install png and freetype libs for matplotlib, which is needed
# by bluesky kml, as well as netcdf and proj libs
RUN apt-get install -y \
        libpng-dev \
        libfreetype6-dev \
        libnetcdf-dev \
        libproj-dev

# Install numpy (which must be installed first); gdal, it's python bindings,
# and it's utilities; and xml libs
RUN apt-get install -y \
        python3-numpy \
    && apt-get install -y \
        libgdal-dev \
        nco \
    && apt-get install -y \
        python3-gdal \
    && apt-get install -y \
        libxml2-dev \
        libxslt1-dev \
    && apt-get install -y \
        gdal-bin # install gdal-bin for gdalwarp and gdal_translate

# mapserver and mapscript are needed to lookup ecoregion in consume, if fire
# doesn't already have it defined.
# TODO: figure out way to install mapscript for python 3, and install it with
# `mapserver-bin`. I tried:
#   1) `apt` to install python-mapscript
#         RUN apt-get install -y \
#             python-mapscript
#      but this is the python 2 binding
#   2) Using alternate PPA, gwibber-daily/ppa, to install ubuntugis-stable
#      a) tried add-apt-repository
#           RUN add-apt-repository ppa:gwibber-daily/ppa \
#               && apt-get update \
#               && apt-get install -y ubuntugis-stable
#         but this failed because add-apt-repository doesn't exist
#      b) tried manually adding repository:
#           RUN echo 'deb http://ppa.launchpad.net/ubuntugis/ppa/ubuntu trusty main' >> /etc/apt/sources.list \
#               && echo 'deb-src http://ppa.launchpad.net/ubuntugis/ppa/ubuntu trusty main' >> /etc/apt/sources.list \
#               && apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 089EBE08314DF160 \
#               && apt-get update \
#               && apt-get install -y ubuntugis-stable
#         but this failed on the `apt-get install` command with
#         `E: Unable to locate package ubuntugis-unstable` errlr
