# Container to run bluesky
FROM bluesky-base

# Notes:
#  - if you don't specify gdal==1.11.3, version pip will try to install version
#    2.* for rasterstats, which will fail.
#  - if you don't specify bluesky version, and if you've already built the
#    complete docker image, a cached older version of bluesky will be
#    included in the image
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple bluesky==1.0.5

### To install from github instead of from AirFire's pypi server
# RUN pip3 install --no-binary gdal  \
#     --trusted-host pypi.smoke.airfire.org \
#     -i http://pypi.smoke.airfire.org/simple \
#     https://github.com/pnwairfire/bluesky/archive/branch-name.tar.gz \
#     gdal==1.11.3

# Install bluesky utils for merging emissions, etc.
RUN pip3 install --trusted-host pypi.smoke.airfire.org \
    -i http://pypi.smoke.airfire.org/simple blueskyutils>=0.1.2

# There's a bug in the bluesky installation that results in missing
# auxliary files.  Manually copy these into the bluesky image:
COPY bluesky/dispersers/vsmoke/images/* \
    /usr/local/lib/python3.5/dist-packages/bluesky/dispersers/vsmoke/images/
COPY bluesky/dispersers/hysplit/bdyfiles/* \
    /usr/local/lib/python3.5/dist-packages/bluesky/dispersers/hysplit/bdyfiles/
COPY bluesky/ecoregion/data/* \
    /usr/local/lib/python3.5/dist-packages/bluesky/ecoregion/data/

# default command is to display bsp help string
CMD ["bsp", "-h"]
