from distutils.core import setup

# Note: using pip.req.parse_requirements like so:
#  > REQUIREMENTS = [str(ir.req) for ir in parse_requirements('requirements.txt')]
# results in the folloing error on Heroku:
#    TypeError: parse_requirements() missing 1 required keyword argument: 'session'
with open('requirements.txt') as f:
    REQUIREMENTS = f.read().splitlines()

setup(
    name='pyairfire',
    version='4.0.0',
    author='Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=[
        'bluesky'
    ],
    scripts=[
        'bin/bsp'
    ],
    url='git@bitbucket.org:fera/airfire-pyairfire.git',
    description='General toolbox of pythong utilities for AirFire team.',
    install_requires=REQUIREMENTS,
)
