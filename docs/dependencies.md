# External Dependencies

As described in the [installation doc](installation.md), there
are three ways to install bluesky - cloning the repo, using pip, and
using docker.  If you choose docker, you'll only need to install docker
itself.  Otherwise, you'll need the various executables, packages,
and libraries listed on this page, depending on what modules you run.


## Python

This package was originally developed to support python 2.7, but has since
been refactored to support 3.5. Attempts to support both 2.7 and 3.5 have
been made but are not guaranteed.

### pip

Install pip3 (with sudo if necessary):

    apt-get install python3-pip


## Module specific dependencies

### fuelbeds

For the fuelbeds module, you'll need to manually install some
dependencies needed by the fccsmap package, which fuelbeds uses.
See the [fccsmap github page](https://github.com/pnwairfire/fccsmap)
for instructions.

Additionally, on ubuntu, you'll need to install libxml

    sudo apt-get install libxml2-dev libxslt1-dev

### localmet

The localmet module relies on the fortran arl profile utility. It is
expected to reside in a directory in the search path. To obtain `profile`,
contact NOAA.

### Plumerise

#### FEPS

If running FEPS plumerise, you'll need the feps_weather and feps_plumerise
executables. They are expected to reside in a directory in the search path.
Contact [USFS PNW AirFire Research Team](http://www.airfire.org/) for more
information.

### dispersion

#### hysplit

If running hysplit dispersion, you'll need to obtain hysplit from NOAA. To obtain
it, go to their [hysplit distribution page](http://ready.arl.noaa.gov/HYSPLIT.php).
Additionally, you'll need the following executables:

 - ```ncea```:  ...
 - ```ncks```:  ...
 - ```hycs_std[-v5.2.3]```: hysplit executable
 - ```hycm_std[-v5.2.3]```: multi-processor hysplit executable
 - ```hyts_std[-v5.2.3]```: hysplit trajectories executable
 - ```hytm_std[-v5.2.3]```: multi-processor hysplit trajectories executable
 - ```mpiexec (mpiexec.openmpi, mpiexec.mpich, or mpiexec.hydra)```: needed to run multi-processor hysplit
 - ```hysplit2netcdf```: this is only needed if opting to convert hysplit output to netcdf; to obtain, ...

Each of these executables are assumed to reside in a directory in the search
path. As a security measure, to avoid security vulnerabilities when hsyplit is
invoked by web service requests, these executables may not be configured to
point to relative or absolute paths.

#### vsmoke

If running vsmoke dispersion, you'll need to obtain vsmoke from the US
Forest Service.  You can download it
[here](http://webcam.srs.fs.fed.us/tools/vsmoke/download.shtml).
As with the hysplit executables, the vsmoke binaries (```vsmoke``` and
```vsmkgs```) are assumed to reside in a directory in the search path.



