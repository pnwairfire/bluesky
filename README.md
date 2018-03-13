# BlueSky Pipeline

BlueSky Framework rearchitected as a pipeable collection of standalone modules.

***This software is provided for research purposes only. It's output may
not accurately reflect actual smoke due to numerous reasons. Data are
provisional; use at own risk.***





## Python 2 and 3 Support

This package was originally developed to support python 2.7, but has since
been refactored to support 3.5. Attempts to support both 2.7 and 3.5 have
been made but are not guaranteed.





## External Dependencies

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
 - ```hycs_std```: hysplit executable
 - ```mpiexec```: this is only needed if opting to run multi-processor hysplit; to obtain ...
 - ```hycm_std```: this is only needed if opting to run multi-processor hysplit; to obtain ...
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





## Development

### Clone Repo

Via ssh:

    git clone git@github.com:pnwairfire/bluesky.git

or http:

    git clone https://github.com/pnwairfire/bluesky.git

### Install python Dependencies

First, install pip (with sudo if necessary):

    apt-get install python-pip


Run the following to install python dependencies:

    pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org -r requirements.txt

Run the following to install packages required for development and testing:

    pip install -r requirements-test.txt
    pip install -r requirements-dev.txt

#### Notes

##### pip issues

If you get an error like    ```AttributeError: 'NoneType' object has no
attribute 'skip_requirements_regex```, it means you need in upgrade
pip. One way to do so is with the following:

    pip install --upgrade pip

##### gdal issues

If, when you use fccsmap, you get the following error:

    *** Error: No module named _gdal_array

it's because your osgeo package (/path/to/site-packages/osgeo/) is
missing _gdal_array.so.  This happens when gdal is built on a
machine that lacks numpy.  The ```--no-binary :all:``` in the pip
install command, above, is meant to fix this issue.  If it doesn't work,
try uninstalling the gdal package and then re-installing it individually
with the ```--no-binary``` option to pip:

    pip uninstall -y GDAL
    pip install --no-binary :all: gdal==1.11.2

If this doesn't work, uninstall gdal, and then install it manually:

    pip uninstall -y GDAL
    wget https://pypi.python.org/packages/source/G/GDAL/GDAL-1.11.2.tar.gz
    tar xzf GDAL-1.11.2.tar.gz
    cd GDAL-1.11.2
    python setup.py install

### Setup Environment

This project contains a single package, ```bluesky```. To import bluesky
package in development, you'll have to add the repo root directory to the
search path. The ```bsp``` script does this automatically, if
necessary.





## Running tests

Use pytest:

    py.test
    py.test test/bluesky/path/to/some_tests.py

You can also use the ```--collect-only``` option to see a list of all tests.

    py.test --collect-only

See [pytest](http://pytest.org/latest/getting-started.html#getstarted) for more information about using pytest.





## Testing export emails

requirements-dev.txt includes the maildump package, which has an smtp server
that you cah use to catch and thus test export emails.  Once you've installed
the package, you can run the server with

    python -m maildump_runner.__main__

Theoretically, you should be able to run it by simply invoking ```maildump```,
but that doesn't seem to always work within virtual environments (e.g. if you
use pyenv + virtualenv).





## Installation

### Installing With pip

First, install pip (with sudo if necessary):

    apt-get install python-pip
    pip install --upgrade pip

Then, to install, for example, v3.0.3, use the following (with sudo if necessary):

    pip install --no-binary gdal --trusted-host pypi.smoke.airfire.org --extra-index http://pypi.smoke.airfire.org/simple bluesky==3.0.3

Or, if using the bluesky package in another project, add it to your project's
requirements.txt:

    --extra-index http://pypi.smoke.airfire.org/simple/
    bluesky==3.0.3

See the Development > Install Dependencies > Notes section, above, for
notes on resolving pip and gdal issues.





## Other Documentation

The rest of BlueSky's documentation can be found under the `docs/`
dir in this repo.

 - [usage](docs/usage)
 - [input data](docs/input-data.md)
 - [configuration](docs/configuration.md)
 - [datetime substitutions](docs/datetime-substitutions.md)
 - [running bsp with docker](docs/docker.md)
 - [examples](docs/examples.md)
