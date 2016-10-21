#!/usr/bin/env python

__author__ = "Joel Dubowy"

import logging
import os
import subprocess
import sys
import traceback

import afscripting

DEFAULT_BIN_DIR = os.path.join(os.path.expanduser("~"), 'bin')
REQUIRED_ARGS = []
OPTIONAL_ARGS = [
    {
        'short': '-n',
        'long': '--image-name',
        'help': "name for image (default: 'bluesky')",
        'default': 'bluesky'
    },
    {
        'short': '-b',
        'long': '--bin-dir',
        'help': "dir containing exe's to copy to image; default: {}".format(
            DEFAULT_BIN_DIR),
        'default': DEFAULT_BIN_DIR
    }
]

EXAMPLES_STR = """
Examples:
  $ ./dev/scripts/docker/build-docker-image.py --log-level=DEBUG
  $ ./dev/scripts/docker/build-docker-image.py --log-level=DEBUG -n foo-bluesky
 """

BINARIES = [
    'profile',
    'hycm_std',
    'hycs_std',
    'hysplit2netcdf',
    'vsmoke',
    'vsmkgs',
    'feps_plumerise',
    'feps_weather'
]

REPO_ROOT_DIR = os.path.abspath(os.path.join(__file__, '../../../..'))

FINAL_INSTRUCTIONS = """
    To upload:
        docker tag {image_name} pnwairfire/bluesky:latest
        docker tag {image_name} pnwairfire/bluesky:v<VERSION>
        docker push pnwairfire/bluesky:latest
        docker push pnwairfire/bluesky:v<VERSION>
"""

def _call(cmd_args):
    logging.info("Calling: {}".format(' '.join(cmd_args)))
    r = subprocess.call(cmd_args)
    if r:
        afscripting.utils.exit_with_msg(
            "Command '{}' returned error code {}".format(' '.join(cmd_args), r),
            exit_code=r)

def _check_binaries_list(args):
    # make sure bin dir exists and that each exe exists
    if not os.path.isdir(args.bin_dir):
        afscripting.utils.exit_with_msg("bin dir {} does not exist".format(
            args.bin_dir))

    for b in BINARIES:
        pathname = os.path.join(args.bin_dir, b)
        if not os.path.isfile(pathname):
            afscripting.utils.exit_with_msg(
                "binary {} does not exist".format(pathname))

def _pre_clean():
    # TODO: call:
    #    docker ps -a | awk 'NR > 1 {print $1}' | xargs docker rm
    # _call(["docker", "ps", "-a", "|", "awk", "'NR", ">", "1", "{print", "$1}'",
    #     "|", "xargs", "docker", "rm"])
    pass

def _build(args):
    dockerfile_pathname = os.path.join(REPO_ROOT_DIR, 'docker', 'Dockerfile')
    _call(['docker','build', '-t', args.image_name, '-f', dockerfile_pathname,
        REPO_ROOT_DIR])

def _create(args):
    _call(['docker', 'create', '--name', args.image_name, args.image_name])

def _copy_binaries(args):
    for b in BINARIES:
        src = os.path.join(args.bin_dir, b)
        dest = '{}:/usr/local/bin/{}'.format(args.image_name, b)
        _call(['docker', 'cp', src, dest])

def _commit(args):
    _call(['docker', 'commit', args.image_name, args.image_name])

def _post_clean():
    # TODO: call:
    #   docker images | grep "<none>" | awk '{print $3}' | xargs docker rmi
    pass

def _print_final_instructions(args):
    sys.stdout.write(FINAL_INSTRUCTIONS.format(image_name=args.image_name))

if __name__ == "__main__":
    parser, args = afscripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)

    _check_binaries_list(args)

    _pre_clean()

    _build(args)
    _create(args)
    _copy_binaries(args)
    _commit(args)

    _post_clean()

    _print_final_instructions(args)
