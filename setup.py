from setuptools import setup, find_packages

from bluesky import __version__

test_requirements = []
with open('requirements-test.txt') as f:
    test_requirements = [r for r in f.read().splitlines()]

setup(
    name='bluesky',
    version=__version__,
    author='Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=find_packages(),
    scripts=[
        'bin/bsp'
    ],
    url='https://github.com/pnwairfire/bluesky',
    description='BlueSky Framework rearchitected as a pipeable collection of standalone modules.',
    install_requires=[
        # Note: gdal needs to be specified here, even though it's specified in
        # fccsmap's dependencies.  For some reason, if not specified here, the
        # osgeo installtion ends up missing osgeo/_gdal_array.so
        "gdal==1.11.2",
        "pyairfire>=0.7.0",
        "eflookup>=0.6.2",
        "emitcalc>=0.3.2",
        "fccsmap>=0.1.6",
        "apps-consume4>=4.1.2"
    ],
    dependency_links=[
        "https://pypi.smoke.airfire.org/simple/pyairfire/",
        "https://pypi.smoke.airfire.org/simple/eflookup/",
        "https://pypi.smoke.airfire.org/simple/emitcalc/",
        "https://pypi.smoke.airfire.org/simple/fccsmap/",
        "https://pypi.smoke.airfire.org/simple/apps-consume4/"
    ],
    tests_require=test_requirements
)
