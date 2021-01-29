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


FROM ubuntu:20.04
MAINTAINER Joel Dubowy


## Install Dependencies

# Install
#  - base dependencies and utilities
#  - png and freetype libs for matplotlib, which is needed
#    by bluesky kml, as well as netcdf and proj libs
#  - numpy
#  - gdal, it's python bindings, and it's utilities
#  - xml libs
#  - gdal-bin for gdalwarp and gdal_translate
#  - openpmi and mpich libs (TODO: install libopenmpi1.10
#    and libmpich12 instead of the dev versions?)
RUN apt-get update \
    && TZ=America/Los_Angeles DEBIAN_FRONTEND=noninteractive apt-get install -y\
        g++ \
        gcc \
        make \
        ssh \
        vim \
        dialog \
        less \
        python3 \
        python3-dev \
        python3-pip \
        libpng-dev \
        libfreetype6-dev \
        libnetcdf-dev \
        libproj-dev \
        python3-numpy \
        libgdal-dev \
        nco \
        python3-gdal \
        libxml2-dev \
        libxslt1-dev \
        gdal-bin \
        libopenmpi-dev \
        libmpich-dev \
        openmpi-bin

# upgrade distribute and pip
# RUN pip3 install --upgrade distribute pip

# blueskykml, consume, and fiona are relatively static these days; so, install
# them here in order to avoid reinstalling them and their large dependencies
# each time other dependencies in requirements.txt change.
# Also install blueskyutils for merging emissions, etc.
# Notable sub-dependencies:
#  - blueskykml:  Pillow==2.8.1, 9.0MB, and matplotlib==1.4.3, 50.4MB
#  - consume:  pandas, etc.
#  - fiona:  39.7MB for fiona itself
# Note: this RUN command will need to be updated if fiona,
#   consume, blueskykml, or blueskyutils are ever updated in setup.py
# Another Note: matplotlib must be explicitly installed to make
#   sure the correct version is installed
RUN pip3 install matplotlib==3.3.4 \
    && pip3 install Fiona==1.8.18 \
    && pip3 install --index-url https://pypi.airfire.org/simple \
        apps-consume==5.0.2 \
        blueskykml==3.0.0 \
        blueskyutils

# Install binary dependencies - for localmet, plumerise,
# dipersion, and visualization
COPY bin/feps_emissions /usr/local/bin/feps_emissions
COPY bin/feps_plumerise /usr/local/bin/feps_plumerise
COPY bin/feps_timeprofile /usr/local/bin/feps_timeprofile
COPY bin/feps_weather /usr/local/bin/feps_weather
COPY bin/hycm_std /usr/local/bin/hycm_std
COPY bin/hycs_std /usr/local/bin/hycs_std
COPY bin/hyts_std /usr/local/bin/hyts_std
COPY bin/hysplit2netcdf /usr/local/bin/hysplit2netcdf
COPY bin/profile /usr/local/bin/profile
COPY bin/bulk_profiler_csv /usr/local/bin/bulk_profiler_csv
COPY bin/vsmkgs /usr/local/bin/vsmkgs
COPY bin/vsmoke /usr/local/bin/vsmoke
COPY bin/makepolygons /usr/local/bin/makepolygons

# Install python dependencies
RUN mkdir /tmp/bluesky/
WORKDIR /tmp/bluesky/
COPY requirements-test.txt /tmp/bluesky/requirements-test.txt
RUN pip3 install -r requirements-test.txt
COPY requirements-dev.txt /tmp/bluesky/requirements-dev.txt
RUN pip3 install -r requirements-dev.txt
COPY requirements.txt /tmp/bluesky/requirements.txt
RUN pip3 install --no-binary gdal -r requirements.txt

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
