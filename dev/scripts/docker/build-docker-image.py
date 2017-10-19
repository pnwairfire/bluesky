#!/usr/bin/env python

__author__ = "Joel Dubowy"

import logging
import os
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

def _build(args):
    dockerfile_pathname = os.path.join(REPO_ROOT_DIR, 'Dockerfile')
    _call(['docker','build', '-t', args.image_name, REPO_ROOT_DIR])

def _tag(args):
    _call(['docker', 'tag', args.image_name, 'pnwairfire/bluesky:latest'])
    _call(['docker', 'tag', args.image_name, 'pnwairfire/bluesky:v' + __version__])

def _push(args):
    sys.stdout.write('Push to hub.docker.com?: [y/N]: ')
    r = input().strip()
    if r and r.lower() in ('y', 'yes'):
        logging.info("Pushing to docker up")
        _call(['docker', 'push', 'pnwairfire/bluesky:latest'])
        _call(['docker', 'push', 'pnwairfire/bluesky:v' + __version__])

if __name__ == "__main__":
    parser, args = afscripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)
    _build(args)
    _tag(args)
    _push(args)
