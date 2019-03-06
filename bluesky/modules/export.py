"""bluesky.modules.export"""

__author__ = "Joel Dubowy"

__all__ = [
    'run'
]

__version__ = "0.1.0"

from bluesky.exceptions import BlueSkyConfigurationError
from bluesky.exporters import emailer, uploader, localsaver

EXPORTERS = {
    'email': emailer.EmailExporter,
    'upload': uploader.UploadExporter,
    'localsave': localsaver.LocalSaveExporter
}

def run(fires_manager):
    """runs the export module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    modes = [m.lower() for m in
        fires_manager.get_config_value('export', 'modes')]
    fires_manager.processed(__name__, __version__, modes=modes)

    extra_exports = fires_manager.get_config_value('export', 'extra_exports')

    exporters = []
    for mode in modes:
        exporter_klass = EXPORTERS.get(mode)
        if not exporter_klass:
            raise BlueSkyConfigurationError("Invalid exporter - {}".format(
                exporter_klass))

        exporter_config = fires_manager.get_config_value('export', mode)
        exporters.append(exporter_klass(extra_exports, exporter_config))

    # Note: export modules update fires_manager with export info, since that
    # info needs to be in the fires_manager before it's dumped to json
    for exporter in exporters:
        exporter.export(fires_manager)
