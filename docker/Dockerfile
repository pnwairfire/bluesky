# A server to run bluesky
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

RUN pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple bluesky

### To install from github instead of from AirFire's pypi server
#RUN pip install --no-binary gdal  --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple   https://github.com/pnwairfire/bluesky/archive/branch-name.tar.gz

CMD ["bsp", "-h"]
