#!/usr/bin/env python

__author__ = "Joel Dubowy"
__copyright__ = "Copyright 2015, AirFire, PNW, USFS"

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
        'long': '--modules',
        'help': 'modules to run',
        'action': 'append',
        'default': []
    },
    {
        'short': '-o',
        'long': '--output-dir',
        'help': "where to record output (if modules produce any); default: $HOME",
        'default': '$HOME'
    }
]

OPTIONAL_ARGS = [
    {
        'short': '-p',
        'long': '--pretty-format',
        'help': "format json output",
        'action': 'store_true'
    },
    {
        'short': '-d',
        'long': '--mount-dir',
        'help': "extra directories to mount in container",
        'action': 'append',
        'default': []
    }
    # TODO: add --met-dir (to mount)
]


EXAMPLES_STR = """This script updates the arl index with the availability of
a particular domain on the current server.

Examples:
  $ ./test/scripts/run-in-docker.py -i /path/to/fire.json \\
      -r /path/to/bluesky/repo/ \\
      -m ingestion fuelbeds consumption emissions

Note about volumes and mounting: mounting directories outside of home
directory seems to results in the directories appearing empty in the container.
Whether this is by design or not, you apparantly need to mount directories
under your home directory.  Sym links don't mount either, so you have to
cp or mv directories under your home dir in order to mount them.
 """


if __name__ == "__main__":
    parser, args = scripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)

    # TODO: if repo root is in args.input_file, replace it with ''

    try:
        input_file = os.path.abspath(args.input_file)

        # TODO: mount met dir if args.met_dir is defined
        cmd_args = [
            'cat', input_file,'|',
            'docker', 'run', '-i',
            '-v', '{}:/bluesky-repo/'.format(args.repo_root),
            '-w', '/bluesky-repo/',
            '-v', '{output_dir}:{output_dir}'.format(output_dir=args.output_dir)
        ]
        for d in args.mount_args:
            dirs = d.split(':')
            h, c = (dirs[0], dirs[1]) if len(dirs) == 2 else (dirs, dirs)
            cmd_args.extend([
                '-v', '{}:{}'.format(h, c)
            ])
        cmd_args.extend([
            'bluesky-base',
            './bin/bsp'
        ])
        cmd_args.extend(args.modules)
        if args.pretty_format:
            cmd_args.extend(['|', 'python', '-m', 'json.tool'])
        cmd = ' '.join(cmd_args)
        logging.debug('Command: {}'.format(cmd))
        # Note: there are security vulnerabilitys with using shell=True,
        #  but it's not an issue for a test script like this
        subprocess.call(cmd, shell=True)

    except Exception, e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        scripting.utils.exit_with_msg(e)
