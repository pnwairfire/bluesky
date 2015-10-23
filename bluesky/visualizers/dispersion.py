"""bluesky.visualizers.disersion"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"


__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__all__ = [
    'HysplitVisualizer'
]
__version__ = "0.1.0"

from collections import namedtuple

from blueskykml import (
    makedispersionkml, makeaquiptdispersionkml, configuration,
    __version__ as blueskykml_version
)

from bluesky.exceptions import BlueSkyConfigurationError

ARGS = [
    "output_directory", "configfile",
    "prettykml", "verbose", "config_options",
    "inputfile","fire_locations_csv",
    "fire-events-csv", "smoke-dispersion-kmz-file",
    "fire-kmz-file","layer"
]
BlueskyKmlArgs = namedtuple('BlueskyKmlArgs', ARGS)

class HysplitVisualizer(object):
    def __init__(self, output_info, fires, **config):
        self._output_info = output_info
        self._fires = fires
        self._config = config

    def run(self, fires):
        output_directory = output_info['directory']
        if not directory or not os.path.isdir(output_directory):

        args = BlueskyKmlArgs(
            output_directory=...,
            prettykml==...,
            # even though 'layer' is an integer index, the option must be of type
            # string or else config.get(section, "LAYER") will fail with error:
            #  > TypeError: argument of type 'int' is not iterable
            # it will be cast to int if specified
            layer=str(self._config.get('layer'))
        )


        try:
            # TODO: clean up any outputs created?  Should this be toggleable via command line option?
            if args.aquipt:
                makeaquiptdispersionkml.main(args)
            else:
                makedispersionkml.main(args)
        except configuration.ConfigurationError, e:
            raise BlueSkyConfigurationError(".....")

        return {
            'blueskykml_version': blueskykml_version,
            ....
        }