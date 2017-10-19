#!/usr/bin/env python

__author__ = "Joel Dubowy"

import logging
import os
import re
import subprocess
import sys
import traceback

import afscripting

try:
    from bluesky import  __version__
except:
    root_dir = os.path.abspath(os.path.join(sys.path[0], '../'))
    sys.path.insert(0, root_dir)
    from bluesky import __version__

REQUIRED_ARGS = []
OPTIONAL_ARGS = [
    {
        'short': '-n',
        'long': '--image-name',
        'help': "name for image (default: 'bluesky')",
        'default': 'bluesky'
    }
]

EXAMPLES_STR = """
Examples:
  $ ./dev/scripts/docker/build-docker-image.py --log-level=DEBUG
  $ ./dev/scripts/docker/build-docker-image.py --log-level=DEBUG -n foo-bluesky
 """

REPO_ROOT_DIR = os.path.abspath(os.path.join(__file__, '../../../..'))

FINAL_INSTRUCTIONS = """
    To upload:
""".format(version=__version__)

def _call(cmd_args):
    logging.info("Calling: {}".format(' '.join(cmd_args)))
    r = subprocess.call(cmd_args)
    if r:
        afscripting.utils.exit_with_msg(
            "Command '{}' returned error code {}".format(' '.join(cmd_args), r),
            exit_code=r)

def build(image_name):
    dockerfile_pathname = os.path.join(REPO_ROOT_DIR, 'Dockerfile')
    _call(['docker','build', '-t', image_name, REPO_ROOT_DIR])

def tag(image_name):
    tag_version = None
    while not tag_version or not re.compile('^v\d+\.\d+\.\d+$').match(tag_version):
        if tag_version:
            sys.stdout.write("Enter a tag version of the form 'v{}' or press"
                " enter to use the default\n".format(__version__))
        sys.stdout.write('Tag version [v{}]: '.format(__version__))
        tag_version = input().strip() or 'v' + __version__
    _call(['docker', 'tag', image_name, 'pnwairfire/bluesky:latest'])
    _call(['docker', 'tag', image_name, 'pnwairfire/bluesky:' + tag_version])
    return tag_version

def upload(tag_version):
    sys.stdout.write('Upload to hub.docker.com?: [y/N]: ')
    r = input().strip()
    if r and r.lower() in ('y', 'yes'):
        logging.info("Pushing to docker up")
        _call(['docker', 'push', 'pnwairfire/bluesky:latest'])
        _call(['docker', 'push', 'pnwairfire/bluesky:' + tag_version])

if __name__ == "__main__":
    parser, args = afscripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)
    build(args.image_name)
    tag_version = tag(args.image_name)
    upload(tag_version)
