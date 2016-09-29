# Container with bluesky and all of it's dependencies.
#
# Example of how to use in dev environment, assuming you've built the
# image with tag 'bluesky':
#
#   docker run --rm -i \
#      -v /path/to/bluesky/repo/:/bluesky/ \
#      -e PYTHONPATH=/bluesky/ \
#      -e PATH=/bluesky/bin/:$PATH \
#      -w /bluesky/ \
#      bluesky ./bin/bsp ...
#
# And an example of how to use already installed bsp
#
#  docker run --rm -i bluesky bsp ...


FROM ubuntu:16.04
MAINTAINER Joel Dubowy


## Install Dependencies

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

RUN pip3 install --upgrade pip

# blueskykml is relatively static these days; so, install it here in order
# to avoid reinstalling it and it's large dependencies (Pillow==2.8.1, 9.0MB,
# and matplotlib==1.4.3, 50.4MB) everytime the the bluesky image is built
# NOTE: this RUN command will need to be updated if 'blueskykml' is ever
#   updated in setup.py
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple blueskykml==1.*

## Install The bluesky Package

# Notes:
#  - if you don't specify gdal==1.11.3, version pip will try to install version
#    2.* for rasterstats, which will fail.
#  - if you don't specify bluesky version, and if you've already built the
#    complete docker image, a cached older version of bluesky will be
#    included in the image
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple bluesky==2.2.2

### To install from github instead of from AirFire's pypi server
# RUN pip3 install --no-binary gdal  \
#     --trusted-host pypi.smoke.airfire.org \
#     -i http://pypi.smoke.airfire.org/simple \
#     https://github.com/pnwairfire/bluesky/archive/branch-name.tar.gz \
#     gdal==1.11.3

# Install bluesky utils for merging emissions, etc.
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple blueskyutils>=0.1.2

# # There's a bug in the bluesky installation that results in missing
# # auxliary files.  Manually copy these into the bluesky image:
# COPY bluesky/dispersers/vsmoke/images/* \
#     /usr/local/lib/python3.5/dist-packages/bluesky/dispersers/vsmoke/images/
# COPY bluesky/dispersers/hysplit/bdyfiles/* \
#     /usr/local/lib/python3.5/dist-packages/bluesky/dispersers/hysplit/bdyfiles/
# COPY bluesky/ecoregion/data/* \
#     /usr/local/lib/python3.5/dist-packages/bluesky/ecoregion/data/

# default command is to display bsp help string
CMD ["bsp", "-h"]
