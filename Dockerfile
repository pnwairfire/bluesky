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


FROM ubuntu:24.04
MAINTAINER Joel Dubowy


## Install Dependencies

# Install python first, so that v3.12 gets installed.  For some reason,
# if python3, python3-dev, and python3-pip are installed along with g++,
# gcc, etc. (below), v 3.10 gets installed
RUN apt-get update \
    && TZ=America/Los_Angeles DEBIAN_FRONTEND=noninteractive apt-get install -y \
        python3 \
        python3-dev \
        python3-pip

# Install numpy==2.1.1. Otherwise, something in the next apt-get install call
# installs numpy==1.26.4
RUN pip3 install --break-system-packages numpy==2.1.1

# Install
#  - base dependencies and utilities
#  - png and freetype libs for matplotlib, which is needed
#    by bluesky kml, as well as netcdf and proj libs
#  - gdal and it's utilities
#  - xml libs
#  - gdal-bin for gdalwarp and gdal_translate
#  - openpmi and mpich libs (TODO: install libopenmpi1.10
#    and libmpich12 instead of the dev versions?)
RUN apt-get update \
    && TZ=America/Los_Angeles DEBIAN_FRONTEND=noninteractive apt-get install -y \
        g++ \
        gcc \
        make \
        ssh \
        vim \
        dialog \
        less \
        libpng-dev \
        libfreetype6-dev \
        libnetcdf-dev \
        libproj-dev \
        libgdal-dev \
        nco \
        libxml2-dev \
        libxslt1-dev \
        gdal-bin \
        mpich \
        libmpich-dev \
        libmpich12 \
        libopenmpi-dev \
        libopenmpi3 \
        openmpi-bin \
        openmpi-common

# Without the following, GDAL gets installed without `_gdal_array`, possibly
# being build with an older version of numpy (?), which breaks blueskykml.
# See: https://stackoverflow.com/questions/75372275/importerror-cannot-import-name-gdal-array-from-osgeo
# and https://gis.stackexchange.com/questions/83138/cannot-import-gdal-array
RUN pip3 install --break-system-packages --no-cache-dir --force-reinstall 'GDAL[numpy]==3.8.4'

# upgrade distribute and pip
# RUN pip3 install --upgrade distribute pip

RUN mkdir /tmp/bluesky/
WORKDIR /tmp/bluesky/
COPY constraints.txt /tmp/bluesky/constraints.txt

# blueskykml, consume, and fiona are relatively static these days; so, install
# them here in order to avoid reinstalling them and their large dependencies
# each time other dependencies in requirements.txt change.
# Notable sub-dependencies:
#  - blueskykml:  Pillow==10.4.0, ~9.0MB, and matplotlib==3.9.2, ~50.4MB
#  - consume:  pandas, etc.
#  - fiona:  39.7MB for fiona itself
# Note: this RUN command will need to be updated if fiona,
#   consume, or blueskykml are ever updated in setup.py
# Another Note: matplotlib must be explicitly installed to make
#   sure the correct version is installed
# Another Note: without --break-system-packages, pip install fails with
#   a message about using virtual environments.  This docker image
#   is soley for bluesky, so we're installing system wide.
RUN pip3 install --break-system-packages numpy==2.1.1 \
    && pip3 install --break-system-packages matplotlib==3.9.2 \
    && pip3 install --break-system-packages fiona==1.10.1 \
    && pip3 install --break-system-packages \
        -c constraints.txt --index-url https://pypi.airfire.org/simple \
        apps-consume==5.3.1 \
        blueskykml==6.0.1

# Install python dependencies
COPY requirements-test.txt /tmp/bluesky/requirements-test.txt
RUN pip3 install --break-system-packages -c constraints.txt -r requirements-test.txt
COPY requirements-dev.txt /tmp/bluesky/requirements-dev.txt
RUN pip3 install --break-system-packages -c constraints.txt -r requirements-dev.txt
COPY requirements.txt /tmp/bluesky/requirements.txt
RUN pip3 install --break-system-packages -c constraints.txt --no-binary gdal -r requirements.txt

# Install binary dependencies - for localmet, plumerise,
# dipersion, and visualization
COPY bin/feps_emissions /usr/local/bin/feps_emissions
COPY bin/feps_plumerise /usr/local/bin/feps_plumerise
COPY bin/feps_timeprofile /usr/local/bin/feps_timeprofile
COPY bin/feps_weather /usr/local/bin/feps_weather
COPY bin/hycm_std-v5.1.0-mpich /usr/local/bin/hycm_std-v5.1.0-mpich
COPY bin/hycm_std-v5.1.0-openmpi /usr/local/bin/hycm_std-v5.1.0-openmpi
COPY bin/hycs_std-v5.1.0 /usr/local/bin/hycs_std-v5.1.0
COPY bin/hytm_std-v5.1.0-mpich /usr/local/bin/hytm_std-v5.1.0-mpich
COPY bin/hytm_std-v5.1.0-openmpi /usr/local/bin/hytm_std-v5.1.0-openmpi
COPY bin/hyts_std-v5.1.0 /usr/local/bin/hyts_std-v5.1.0
COPY bin/hycm_std-v5.2.3-mpich /usr/local/bin/hycm_std-v5.2.3-mpich
COPY bin/hycm_std-v5.2.3-openmpi /usr/local/bin/hycm_std-v5.2.3-openmpi
COPY bin/hycs_std-v5.2.3 /usr/local/bin/hycs_std-v5.2.3
COPY bin/hytm_std-v5.2.3-mpich /usr/local/bin/hytm_std-v5.2.3-mpich
COPY bin/hytm_std-v5.2.3-openmpi /usr/local/bin/hytm_std-v5.2.3-openmpi
COPY bin/hyts_std-v5.2.3 /usr/local/bin/hyts_std-v5.2.3
COPY bin/hysplit2netcdf /usr/local/bin/hysplit2netcdf
COPY bin/profile /usr/local/bin/profile
COPY bin/bulk_profiler_csv /usr/local/bin/bulk_profiler_csv
COPY bin/vsmkgs /usr/local/bin/vsmkgs
COPY bin/vsmoke /usr/local/bin/vsmoke
COPY bin/makepolygons /usr/local/bin/makepolygons

# Install bluesky package
COPY bluesky/ /tmp/bluesky/bluesky/
COPY bin/ /tmp/bluesky/bin/
COPY setup.py /tmp/bluesky/setup.py
RUN python3 setup.py install
WORKDIR /bluesky/

ARG UNAME=bluesky
ARG UID=0
ARG GID=0
RUN groupadd -g $GID -o $UNAME
RUN useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME
USER $UNAME

# default command is to display bsp help string
CMD ["bsp", "-h"]
