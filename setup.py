from distutils.core import setup

# Note: using pip.req.parse_requirements like so:
#  > REQUIREMENTS = [str(ir.req) for ir in parse_requirements('requirements.txt')]
# results in the folloing error on Heroku:
#    TypeError: parse_requirements() missing 1 required keyword argument: 'session'
with open('requirements.txt') as f:
    REQUIREMENTS = f.read().splitlines()

setup(
    name='BlueSky Pipeline',
    version='0.0.1',
    author='Joel Dubowy',
    author_email='jdubowy@gmail.com',
    packages=[
        'bluesky'
    ],
    scripts=[
        'bin/bsp'
    ],
    url='git@bitbucket.org:fera/airfire-bluesky-pipeline.git',
    description='BlueSky Framework rearchitected as a pipeable collection of standalone modules.',
    install_requires=REQUIREMENTS,
)
