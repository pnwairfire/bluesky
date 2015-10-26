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
        'bin/bsp',
        'bin/bsp-web'
    ],
    package_data={
        # TODO: not sure how to specify package data for nested package.
        #   a)  {'hysplit': ['bdyfiles/*.']}
        #   b)  {'bluesky': ['hysplit/bdyfiles/*.']}
        #   c)  {'bluesky': {'hysplit': ['bdyfiles/*.']} }
        #   d)  some other way?
        'hysplit': ['bdyfiles/*.']
    },
    url='https://github.com/pnwairfire/bluesky',
    description='BlueSky Framework rearchitected as a pipeable collection of standalone modules.',
    install_requires=[
        "pyairfire>=0.8.21",
        "eflookup>=0.6.2",
        "emitcalc>=0.3.2",
        "fccsmap>=0.1.6",
        "timeprofile>=0.1.2",
        "plumerise>=0.1.1",
        "blueskykml>=0.2.5",
        "apps-consume4>=4.1.2",
        "tornado==4.2.1"
    ],
    dependency_links=[
        "https://pypi.smoke.airfire.org/simple/pyairfire/",
        "https://pypi.smoke.airfire.org/simple/eflookup/",
        "https://pypi.smoke.airfire.org/simple/emitcalc/",
        "https://pypi.smoke.airfire.org/simple/fccsmap/",
        "https://pypi.smoke.airfire.org/simple/timeprofile/",
        "https://pypi.smoke.airfire.org/simple/plumerise/",
        "https://pypi.smoke.airfire.org/simple/blueskykml/",
        "https://pypi.smoke.airfire.org/simple/apps-consume4/"
    ],
    tests_require=test_requirements
)
