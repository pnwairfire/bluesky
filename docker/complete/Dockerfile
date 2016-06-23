# Container to run bluesky
FROM bluesky-base

# Notes:
#  - if you don't specify gdal==1.7.3, version pip will try to install version
#    2.* for rasterstats, which will fail.
#  - if you don't specify bluesky version, and if you've already built the
#    complete docker image, a cached older version of bluesky will be
#    included in the image
RUN pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple bluesky==0.9.3 gdal==1.7.3

### To install from github instead of from AirFire's pypi server
#RUN pip install --no-binary gdal  --trusted-host pypi.smoke.airfire.org -i http://pypi.smoke.airfire.org/simple   https://github.com/pnwairfire/bluesky/archive/branch-name.tar.gz gdal==1.7.3

CMD ["bsp", "-h"]
