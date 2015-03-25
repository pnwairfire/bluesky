import re
from setuptools import setup, find_packages

from bluesky import __version__

# Note: using pip.req.parse_requirements like so:
#  > REQUIREMENTS = [str(ir.req) for ir in parse_requirements('requirements.txt')]
# results in the folloing error on Heroku:
#    TypeError: parse_requirements() missing 1 required keyword argument: 'session'

git_hg_url_matcher = re.compile('^(git|hg)\+(.+)(github.com|bitbucket.org)/(.+)/([^/.]+)(\.git)?@v?([0-9.]+)$')
def parse_requirements(dep_links, req_file_name):
    with open(req_file_name) as f:
        reqs = []
        for r in f.read().splitlines():
            m = git_hg_url_matcher.match(r)
            if m:
                # When there's a dependency from github.com or bitbucket,
                # we need to add a dependency link that points to
                # a downloadable tarball or zip file and then add the package
                # name (without version specified) to the install_requires
                # see http://peak.telecommunity.com/DevCenter/setuptools#dependencies-that-aren-t-in-pypi
                if 'bitbucket.org' == m.group(3):
                    # m.groups() will be something like the following:
                    #   ('hg', 'https://', 'bitbucket.org', 'fera', 'apps-consume4', None, '4.1.0')
                    # The link to download a tarball of the repo from github
                    # will be something like the following:
                    #   https://bitbucket.org/fera/apps-consume4/get/v4.1.0.zip#egg=apps-consume4
                    dep_links.append('%s%s/%s/%s/get/v%s.zip#egg=%s' % (
                        m.group(2), m.group(3), m.group(4), m.group(5),
                        m.group(7), m.group(5).replace('-','_')))
                else:
                    # m.groups() will be something like the following:
                    #   ('git', 'https://', 'github.com', 'pnwairfire', 'pyairfire', None, '0.6.14')
                    # The link to download a tarball of the repo from github
                    # will be something like the following:
                    #   https://github.com/pnwairfire/pyairfire/tarball/v0.6.14#egg=pyairfire
                    dep_links.append('%s%s/%s/%s/tarball/v%s#egg=%s' % (
                        m.group(2), m.group(3), m.group(4), m.group(5),
                        m.group(7), m.group(5)))
                reqs.append(m.group(5).replace('-','_'))
            else:
                reqs.append(r)
        return reqs

dependency_links = []
requirements = parse_requirements(dependency_links, 'requirements.txt')
test_requirements = parse_requirements(dependency_links, 'requirements-test.txt')

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
    install_requires=requirements,
    dependency_links=dependency_links,
    tests_require=test_requirements
)
