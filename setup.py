from setuptools import setup, find_packages

from bluesky import __version__

requirements = []
with open('requirements.txt') as f:
    requirements = [r for r in f.read().splitlines() if not r.startswith('-')]
test_requirements = []
with open('requirements-test.txt') as f:
    test_requirements = [r for r in f.read().splitlines()]

setup(
    name='bluesky',
    version=__version__,
    license='GPLv3+',
    author='Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=find_packages(),
    scripts=[
        'bin/bsp',
        'bin/bsp-run-info',
        'bin/bsp-output-visualizer',
        'bin/ecoregion-lookup'
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX",
        "Operating System :: MacOS"
    ],
    package_data={
        # TODO: not sure how to specify package data for nested package.
        #   a)  {'hysplit': ['bdyfiles/*.']}
        #   b)  {'bluesky': ['hysplit/bdyfiles/*.']}
        #   c)  {'bluesky': {'hysplit': ['bdyfiles/*.']} }
        #   d)  some other way?
        # Update: the following way seems to be the only way to work both
        # via `python setup.py install` as well as via pip
        'bluesky': [
            'consumption/consume/data/*',
            'dispersers/hysplit/bdyfiles/*',
            'trajectories/hysplit/bdyfiles/*',
            'dispersers/vsmoke/images/*',
            'ecoregion/data/*',
            'fips/*'
        ]
    },
    url='https://github.com/pnwairfire/bluesky',
    description='BlueSky Framework rearchitected as a pipeable collection of standalone modules.',
    install_requires=requirements,
    dependency_links=[
        "https://pypi.airfire.org/simple/pyairfire/",
        "https://pypi.airfire.org/simple/afconfig/",
        "https://pypi.airfire.org/simple/afdatetime/",
        "https://pypi.airfire.org/simple/afscripting/",
        "https://pypi.airfire.org/simple/eflookup/",
        "https://pypi.airfire.org/simple/emitcalc/",
        "https://pypi.airfire.org/simple/fccsmap/",
        "https://pypi.airfire.org/simple/geoutils/",
        "https://pypi.airfire.org/simple/timeprofile/",
        "https://pypi.airfire.org/simple/met/",
        "https://pypi.airfire.org/simple/plumerise/",
        "https://pypi.airfire.org/simple/blueskykml/",
        "https://pypi.airfire.org/simple/apps-consume/"
    ],
    tests_require=test_requirements
)
