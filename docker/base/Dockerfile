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

# Note: upgrade distribute and install png and freetype libs for
#   matplotlib, which is needed by bluesky kml
RUN apt-get update && apt-get install -y g++ gcc make python python-dev python-pip libnetcdf-dev proj nco libpng12-dev libfreetype6-dev
RUN pip install --upgrade pip distribute

# numpy 1.8.0 needs to be installed before libgdal
RUN pip install numpy==1.8.0
RUN apt-get install -y libgdal1-1.7.0
RUN apt-get install -y python-gdal libxml2-dev libxslt1-dev

