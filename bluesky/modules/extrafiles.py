"""bluesky.modules.extrafiles
"""

__author__ = "Joel Dubowy"

__all__ = [
    'run'
]

__version__ = "0.1.0"

import os

from bluesky.config import Config
from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.extrafilewriters import (
    emissionscsv, firescsvs
)

EXTRA_FILE_WRITERS = {
    'emissionscsv': emissionscsv.EmissionsCsvWriter,
    'firescsvs': firescsvs.FiresCsvsWriter
}

def run(fires_manager):
    """runs the extrafiles module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    file_sets = [m.lower() for m in
        Config.get('extrafiles', 'sets')]
    fires_manager.processed(__name__, __version__, sets=file_sets)

    dest_dir = _get_dest_dir(fires_manager)
    writers = get_extra_file_writers(fires_manager, file_sets, dest_dir)

    # fires_manager.extrafiles.output.directory needed by export module
    fires_manager.extrafiles = {
        'output': {
            'directory': dest_dir
        }
    }
    for file_set, writer in writers:
        fires_manager.extrafiles[file_set] = writer.write(fires_manager)

def get_extra_file_writers(fires_manager, file_sets, dest_dir):
    writers = []
    for file_set in file_sets:
        writer_klass = EXTRA_FILE_WRITERS.get(file_set)
        if not writer_klass:
            raise BlueSkyConfigurationError("Invalid writer - {}".format(
                writer_klass))

        writer_config = Config.get('extrafiles', file_set)
        writers.append(
            (file_set, writer_klass(dest_dir, **writer_config))
        )
    return writers

def _get_dest_dir(fires_manager):
    dest_dir = Config.get('extrafiles', 'dest_dir')
    if not dest_dir:
        raise BlueSkyConfigurationError("Specify extrafiles destination dir "
            "('config' > 'extrafiles' > 'dest_dir')")

    dest_dir = os.path.abspath(dest_dir)
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    return dest_dir
