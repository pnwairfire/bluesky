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
# Note: without --break-system-packages, pip install fails with
#   a message about using virtual environments.  This docker image
#   is soley for bluesky, so we're installing system wide.
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

RUN apt remove -y python3-pyparsing python3-blinker


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

# TODO: install dependencies using constraints.txt directly
#     rather than referencing each of the requirements*.txt files?
#  RUN pip3 install --break-system-packages \
#      --extra-index https://pypi.airfire.org/simple/ \
#      -r constraints.txt

# Install consume tarball dirrectly because we get the following error
# when installing from AirFire's pypi server (which we don't get with
# other AirFire packages):
#  ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE. If you have updated the package versions, please update the hashes. Otherwise, examine the package contents carefully; someone may have tampered with them.
#      fera-apps-consume==5.3.2 from https://pypi.airfire.org/packages/simple/fera-apps-consume/fera-apps-consume-5.3.2.tar.gz#sha256=4bdfa4bbf1604873bb2a424190d9eb5812a79a934499afdd240130431b6b3150:
#          Expected sha256 4bdfa4bbf1604873bb2a424190d9eb5812a79a934499afdd240130431b6b3150
#               Got        71de5472888d7b129c9ec35c6d621670ad8b7b78e0f6a869eb2976e706281578

RUN wget https://pypi.airfire.org/packages/simple/apps-consume/apps-consume-5.3.1.tar.gz \
    && pip3 install --break-system-packages \
        --extra-index https://pypi.airfire.org/simple/ \
        -f https://pypi.airfire.org/simple/ \
        apps-consume-5.3.1.tar.gz

# Install python dependencies
COPY requirements-test.txt /tmp/bluesky/requirements-test.txt
RUN pip3 install --break-system-packages -c constraints.txt -r requirements-test.txt
COPY requirements-dev.txt /tmp/bluesky/requirements-dev.txt
RUN pip3 install --break-system-packages -c constraints.txt -r requirements-dev.txt
COPY requirements.txt /tmp/bluesky/requirements.txt
RUN pip3 install --break-system-packages -c constraints.txt --no-binary gdal -r requirements.txt

RUN apt-get update && apt install -y nodejs npm
RUN npm install -g @pnwairfire/piles-calculator@1.0.1

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
ARG UID=1000
ARG GID=1000

# We used to always add a new group, even if the GID was already used:
#    RUN groupadd -g $GID -o $UNAME
# Now we rename the group if GID already exists
RUN if getent group $GID; \
    then \
        echo "Group $GID ($(getent group $GID | cut -d: -f1)) exists. Renaming as $UNAME"; \
        groupmod -n $UNAME "$(getent group $GID | cut -d: -f1)"; \
    else \
        groupadd -g $GID $UNAME; fi

# Similarly, we used to always add a new user, even if the UID was already used:
#    RUN useradd -m -u $UID -g $GID -s /bin/bash -o $UNAME
# Now we rename the user if UID already exists
RUN if id -nu $UID; \
    then \
        echo "User $UID ($(id -nu $UID)) exists. Renaming as $UNAME"; \
        usermod -l $UNAME $(id -nu $UID); \
    else \
        useradd -m -u $UID -g $GID -s /bin/bash $UNAME; fi

USER $UNAME

# default command is to display bsp help string
CMD ["bsp", "-h"]
