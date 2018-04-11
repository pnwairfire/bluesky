"""bluesky.modules.output
"""

__author__ = "Joel Dubowy"

__all__ = [
    'run'
]

__version__ = "0.1.0"

import os

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.outputters import emissionscsv

OUTPUTTERS = {
    'emissionscsv': emissionscsv.EmissionsCsvOutputter
}

def run(fires_manager):
    """runs the output module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    output_sets = [m.lower() for m in
        fires_manager.get_config_value('output', 'sets', default=[])]
    fires_manager.processed(__name__, __version__, sets=output_sets)

    dest_dir = _get_dest_dir(fires_manager)
    outputters = get_outputters(fires_manager, output_sets, dest_dir)

    # Note: output modules update fires_manager with output info, since that
    # info needs to be in the fires_manager before it's dumped to json
    fires_manager.output = {
        'output': {
            'directory': dest_dir
        }
    }
    for output_set, outputter in outputters:
        fires_manager.output[output_set] = outputter.output(fires_manager)

def get_outputters(fires_manager, output_sets, dest_dir):
    outputters = []
    for output_set in output_sets:
        outputter_klass = OUTPUTTERS.get(output_set)
        if not outputter_klass:
            raise BlueSkyConfigurationError("Invalid outputter - {}".format(
                outputter_klass))

        outputter_config = fires_manager.get_config_value(
            'output', output_set, default={})
        outputters.append(
            (output_set, outputter_klass(dest_dir, **outputter_config))
        )
    return outputters

def _get_dest_dir(fires_manager):
    dest_dir = fires_manager.get_config_value('output', 'dest_dir')
    if not dest_dir:
        raise BlueSkyConfigurationError("Specify output destination dir "
            "('config' > 'output' > 'dest_dir')")

    dest_dir = os.path.abspath(dest_dir)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    return dest_dir
