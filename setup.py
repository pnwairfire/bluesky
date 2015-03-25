import re
from distutils.core import setup

from bluesky import __version__

# Note: using pip.req.parse_requirements like so:
#  > REQUIREMENTS = [str(ir.req) for ir in parse_requirements('requirements.txt')]
# results in the folloing error on Heroku:
#    TypeError: parse_requirements() missing 1 required keyword argument: 'session'
git_url_matcher = re.compile('^git\+(.+)/([^/.]+)(\.git)?@v?([0-9.]+)$')
def parse_requirements(dep_links, req_file_name):
    with open(req_file_name) as f:
        reqs = []
        for r in f.read().splitlines():
            m = git_url_matcher.match(r)
            if m:
                # When there's a dependency from github.com (or other git
                # server), we need to add a dependency link that points to
                # a downloadable tarball or zip file and then add the package
                # name (without version specified) to the install_requires
                # see http://peak.telecommunity.com/DevCenter/setuptools#dependencies-that-aren-t-in-pypi
                # TODO: test to see if this url format works for bitbucket as well
                dep_links.append('%s/%s/tarball/v%s#egg=%s' % (
                    m.group(1), m.group(2), m.group(4), m.group(2)))
                reqs.append("%s" % (m.group(2)))
            else:
                reqs.append(r)
        return reqs

dependency_links = []
requirements = parse_requirements(dependency_links, 'requirements.txt')
test_requirements = parse_requirements(dependency_links, 'requirements-test.txt')

setup(
    name='BlueSky Pipeline',
    version=__version__,
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
    install_requires=requirements,
    dependency_links=dependency_links,
    tests_require=test_requirements
)
