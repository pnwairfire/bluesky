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

# TODO: install libopenmpi1.10 and libmpich12 instead of the dev versions
RUN apt-get update \
    && apt-get install -y \
        libopenmpi-dev \
        libmpich-dev \
    && apt-get install -y \
        openmpi-bin

RUN pip3 install --upgrade pip

# blueskykml and consume are relatively static these days; so, install them
# here in order to avoid reinstalling them and their large dependencies
# (Pillow==2.8.1, 9.0MB, and matplotlib==1.4.3, 50.4MB, for blueskykml;
# pandas, etc. for consume) everytime the the bluesky image is built
# NOTE: these RUN commands will need to be updated if 'blueskykml'
#   and/or consume are ever updated in setup.py
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple blueskykml==1.*
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple apps-consume4==4.1.*

RUN apt-get install -y \
        vim

# Install bluesky utils for merging emissions, etc.
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple blueskyutils>=0.2.0

## Install The bluesky Package

RUN mkdir /tmp/bluesky/
WORKDIR /tmp/bluesky/
COPY requirements.txt /tmp/bluesky/requirements.txt
COPY requirements-test.txt /tmp/bluesky/requirements-test.txt
COPY setup.py /tmp/bluesky/setup.py
# copy just __init__.py for now to be able to load setup.py for
# installing dependencies
COPY bluesky/__init__.py /tmp/bluesky/bluesky/__init__.py
RUN pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -r requirements.txt
# now copy over the the rest of the sourve files
COPY bluesky/ /tmp/bluesky/bluesky/
COPY bin/ /tmp/bluesky/bin/
RUN python3 setup.py install


# default command is to display bsp help string
CMD ["bsp", "-h"]
