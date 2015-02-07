#!/usr/bin/env python

"""bsp: Runs BlueSky

Example calls:
 >
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from bluesky.models.fires import Fire, FireDataFormats

REQUIRED_OPTIONS = [
    # TODO: put output (and input) formats in here?
]

OPTIONAL_OPTIONS = [
    {
        'short': '-f',
        'long': '--output-format',
        'dest': 'output_format',
        'help': 'input file comtaining JSON formatted fire data',
        'action': "store",
        'default': None
    },
    {
        'short': '-i',
        'long': '--input-file',
        'dest': 'input_file',
        'help': 'input file comtaining JSON formatted fire data',
        'action': "store",
        'default': None
    },
    {
        'short': '-o',
        'long': '--output-file',
        'dest': 'output_file',
        'help': 'output file comtaining JSON formatted fire data',
        'action': "store",
        'default': None
    },
    {
        'short': '-c',
        'long': '--country-code-whitelist',
        'dest': 'country_code_whitelist',
        'help': 'input file comtaining JSON formatted fire data',
        'action': "append",
        'default': []
    }
]


def main():
    parser, options, args = scripting.options.parse_options(REQUIRED_OPTIONS,
        OPTIONAL_OPTIONS)
    #scripting.options.check_required_options(options, REQUIRED_OPTIONS, parser)
    scripting.options.configure_logging_from_options(options, parser)
    scripting.options.output_options(options)

    try:
        # TODO: either have input format specifeid as an option or
        # update Fire.loads to deduce it from the data
        format = None

        fires_importer = models.fires.FiresImporter(
            options.input_file, options.output_file)
        fires = Fire.loads(format)

        # TODO: apply filter

        output_format = getattr(FireDataFormat, options.output_format)
        fires_importer.dumps(output_format)

    except Exception, e:
        scripting.utils.exit_with_msg(e.message)

if __name__ == "__main__":
    main()
