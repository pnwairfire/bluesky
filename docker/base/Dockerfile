# Server containing all of bluesky's dependencies, to be used
# as dev environment and as base for container in which bluesky
# is to be installed.
#
# Example of how to use in dev environment, assuming image is called
# bluesky-base:
#   docker run -v /path/to/repo/:/path/to/repo/ \
#      bluesky-base /path/to/repo/bin/bluesky

FROM ubuntu:12.04

MAINTAINER Joel Dubowy

RUN apt-get update
RUN apt-get install -y g++ gcc make python python-dev python-pip libnetcdf-dev proj
RUN pip install --upgrade pip
RUN pip install numpy==1.8.0
RUN apt-get install -y libgdal1-1.7.0
#RUN pip install gdal==1.7.0
RUN apt-get install -y python-gdal libxml2-dev libxslt1-dev

# need to upgrade distribute and install png and freetype libs for matplotlib
RUN pip install --upgrade distribute
RUN apt-get install -y libpng12-dev libfreetype6-dev
