#!/usr/bin/env python

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2016, AirFire, PNW, USFS"

import logging
import os
import subprocess
import sys
import traceback

from pyairfire import scripting

DOCKER_IMAGE_NAMES = {
    "base": "bluesky-base",
    "complete": "bluesky"
}
VALID_IMAGES_STR = ', '.join(DOCKER_IMAGE_NAMES.keys())

REQUIRED_ARGS = [
    {
        'short': '-i',
        'long': '--image',
        'help': "docker image to build ({})".format(VALID_IMAGES_STR)
    }
]

DEFAULT_BIN_DIR = os.path.join(os.path.expanduser("~"), 'bin')
OPTIONAL_ARGS = [
    {
        'short': '-n',
        'long': '--image-name',
        'help': "name for image (defaults: {})".format(', '.join([
            k+" -> '"+v +"'" for k,v in DOCKER_IMAGE_NAMES.items()]))
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
Valid images: {valid_images}

Examples:
  $ ./dev/scripts/docker/run-in-docker.py -i complete
 """.format(valid_images=VALID_IMAGES_STR)

BINARIES = [
    'profile',
    'mpiexec',
    'hycm_std',
    'hycs_std',
    'hysplit2netcdf',
    'vsmoke',
    'vsmkgs',
    'feps_plumerise',
    'feps_weather'
]

AUX_FILES = [
    'dispersers/vsmoke/images/',
    'dispersers/hysplit/bdyfiles/',
    'ecoregion/data/'
]

REPO_ROOT_DIR = os.path.abspath(os.path.join(__file__, '../../../..'))

FINAL_INSTRUCTIONS = """
    To upload:
        docker tag -f <IMAGE_ID> pnwairfire/bluesky:latest
        docker tag <IMAGE_ID> pnwairfire/bluesky:v<VERSION>
        docker push pnwairfire/bluesky:latest
        docker push pnwairfire/bluesky:v<VERSION>
"""

def _call(cmd_args):
    logging.info("Calling: {}".format(' '.join(cmd_args)))
    r = subprocess.call(cmd_args)
    if r:
        scripting.utils.exit_with_msg(
            "Command '{}' returned error code {}".format(' '.join(cmd_args), r),
            exit_code=r)

def _check_image(args):
    if args.image not in DOCKER_IMAGE_NAMES:
        scripting.utils.exit_with_msg(
            "Invalid image: {} (valid options: {})".format(
            args.image, VALID_IMAGES_STR))

    args.image_name = args.image_name or DOCKER_IMAGE_NAMES[args.image]

    # TODO: check if image exists; if so, prompt to confirm if user
    #   wants to continue or abort and ddelete first (don't have this script
    #   delete image)

def _check_binaries_list(args):
    # make sure bin dir exists and that each exe exists
    if not os.path.isdir(args.bin_dir):
        scripting.utils.exit_with_msg("bin dir {} does not exist".format(
            args.bin_dir))

    for b in BINARIES:
        pathname = os.path.join(args.bin_dir, b)
        if not os.path.isfile(pathname):
            scripting.utils.exit_with_msg(
                "binary {} does not exist".format(pathname))

def _pre_clean():
    # TODO: call:
    #    docker ps -a | awk 'NR > 1 {print $1}' | xargs docker rm
    # _call(["docker", "ps", "-a", "|", "awk", "'NR", ">", "1", "{print", "$1}'",
    #     "|", "xargs", "docker", "rm"])
    pass

def _build(args):
    pathname = os.path.join(REPO_ROOT_DIR, 'docker', args.image)
    _call(['docker','build', '-t', args.image_name, pathname])

def _create(args):
    _call(['docker', 'create', '--name', args.image_name, args.image_name])

def _copy_binaries(args):
    for b in BINARIES:
        src = os.path.join(args.bin_dir, b)
        dest = '{}:/usr/local/bin/{}'.format(args.image_name, b)
        _call(['docker', 'cp', src, dest])

def _copy_aux_files(args):
    if args.image == 'complete':
        for f in AUX_FILES:
            src = os.path.join(REPO_ROOT_DIR, 'bluesky', f)
            dest = '{}:{}'.format(args.image_name, os.path.join(
                '/usr/local/lib/python2.7/dist-packages/bluesky', f))
            _call(['docker', 'cp', src, dest])

def _commit(args):
    _call(['docker', 'commit', args.image_name, args.image_name])

def _post_clean():
    # TODO: call:
    #   docker images | grep "<none>" | awk '{print $3}' | xargs docker rmi
    pass

def _print_final_instructions(args):
    sys.stdout.write(FINAL_INSTRUCTIONS)

if __name__ == "__main__":
    parser, args = scripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)

    _check_image(args)
    _check_binaries_list(args)

    _pre_clean()

    _build(args)
    _create(args)
    _copy_binaries(args)
    _copy_aux_files(args)
    _commit(args)

    _post_clean()

    _print_final_instructions(args)
