#!/usr/bin/env python

from pyairfire import scripting

REQUIRED_ARGS = [
    {
        'short': '-i',
        'long': '--input-file',
        'help': "json input file, relative to repo root"
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
    }
]
OPTIONAL_ARGS = [
    {
        'short': '-o',
        'long': '--output-dir',
        'help': "where to record output (if modules produce any); default: $HOME",
        'default': '$HOME'
    },
    # TODO: add --met-dir (to mount)
]


EXAMPLES_STR = """This script updates the arl index with the availability of
a particular domain on the current server.

Examples:
  $ ./test/scripts/run-in-docker.py -i rel/path/to/fire.json \\
      -r /path/to/bluesky/repo/ \\
      -m ingestion fuelbeds consumption emissions
 """


if __name__ == "__main__":
    parser, args = scripting.args.parse_args(REQUIRED_ARGS, OPTIONAL_ARGS,
        epilog=EXAMPLES_STR)

    # TODO: if repo root is in args.input_file, replace it with ''

    try:

        # TODO: mount met dir if args.met_dir is defined
        cmd_args = [
            'docker', 'run', '-i',
            '-v', '{}:/bluesky/'.format(args.repo_root),
            '-w' '/bluesky/',
            '-v' '{}:/bluesky-output/'.format(args.output_dir),
            'bluesky-base',
            './bin/bsp/',
            '-i', args.input_file
        ]
        cmd_args.extend(args.modules)
        r = subprocess.check_output(cmd_args)
        sys.stdout.write(r)

    except Exception, e:
        logging.error(e)
        logging.debug(traceback.format_exc())
        scripting.utils.exit_with_msg(e)



