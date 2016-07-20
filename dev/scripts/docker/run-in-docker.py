#!/usr/bin/env python

__author__ = "Joel Dubowy"

import logging
import os
import subprocess
import sys
import traceback

from pyairfire import scripting

REQUIRED_ARGS = [
    {
        'short': '-i',
        'long': '--input-file',
        'help': "json input file"
    },
    {
        'short': '-r',
        'long': '--repo-root',
        'help': "path to repo root"
    },
    {
        'short': '-m',
        'long': '--module',
        'dest': 'modules',
        'help': 'module to run',
        'action': 'append',
        'default': []
    }
]

OPTIONAL_ARGS = [
    {
        'short': '-c',
        'long': '--config-file',
        'help': "json input file"
    },
    {
        'short': '-p',
        'long': '--pretty-format',
        'help': "format json output",
        'action': 'store_true'
    },
    {
        'short': '-d',
        'long': '--mount-dir',
        'dest': 'mount_dirs',
        'help': "extra directories to mount in container",
        'action': 'append',
        'default': []
    }
    # TODO: add --met-dir (to mount)
]


EXAMPLES_STR = """This script updates the arl index with the availability of
a particular domain on the current server.

Examples:
  $ ./dev/scripts/docker/run-in-docker.py \\
      -i /path/to/fire.json \\
      -c /path/to/config.json \\
      -r /path/to/bluesky/repo/ \\
      -d /path/to/met/:/met/ \\
      -d /path/to/output/dir/ \\
      -m ingestion -m fuelbeds -m consumption -m emissions \\
      -m timeprofiling -m findmetdata -m localmet \\


Note about volumes and mounting: mounting directories outside of your home
directory seems to result in the directories appearing empty in the
docker container. Whether this is by design or not, you apparently need to
mount directories under your home directory.  Sym links don't mount either, so
you have to cp or mv directories under your home dir in order to mount them.
 """


if __name__ == "__main__":
    parser, args = scripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)

    # TODO: if repo root is in args.input_file, replace it with ''

    try:
        input_file = os.path.abspath(args.input_file)

        cmd_args = [
            'cat', input_file,'|',
            'docker', 'run', '-i',
            '-v', '{}:/bluesky-repo/'.format(args.repo_root),
            '-w', '/bluesky-repo/'
        ]

        if args.config_file:
            cmd_args.extend(['-c', args.config_file])

        for d in args.mount_dirs:
            dirs = d.split(':')
            h, c = (dirs[0], dirs[1]) if len(dirs) == 2 else (dirs, dirs)
            cmd_args.extend([
                '-v', '{}:{}'.format(h, c)
            ])
        cmd_args.extend([
            'bluesky-base',
            './bin/bsp',
            '--log-level', args.log_level
        ])
        cmd_args.extend(args.modules)
        if args.pretty_format:
            cmd_args.extend(['|', 'python', '-m', 'json.tool'])
        cmd = ' '.join(cmd_args)
        logging.debug('Command: {}'.format(cmd))
        # Note: there are security vulnerabilitys with using shell=True,
        #  but it's not an issue for a test script like this
        subprocess.call(cmd, shell=True)

    except Exception as e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        scripting.utils.exit_with_msg(e)
