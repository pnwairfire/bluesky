"""bluesky.modules.output
"""

__author__ = "Joel Dubowy"

__all__ = [
    'run'
]

__version__ = "0.1.0"

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

    outputters = []
    for output_set in output_sets:
        outputter_klass = OUTPUTTERS.get(output_set)
        if not outputter_klass:
            raise BlueSkyConfigurationError("Invalid outputter - {}".format(
                outputter_klass))

        outputter_config = fires_manager.get_config_value(
            'output', output_set, default={})
        outputters.append(outputter_klass(**outputter_config))

    # Note: output modules update fires_manager with output info, since that
    # info needs to be in the fires_manager before it's dumped to json
    for outputter in outputters:
        outputter.output(fires_manager)
