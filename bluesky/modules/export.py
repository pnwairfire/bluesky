"""bluesky.modules.export"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

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
    mode = fires_manager.get_config_value('export', 'mode',
        default='email').lower()

    exporter_klass = EXPORTERS.get('mode'):
    if not exporter_klass:
        raise BlueSkyConfigurationError("Invalid exporter - {}".format()
            exporter_klass)

    extra_exports = fires_manager.get_config_value('export', 'extra_exports', default=[])
    exporter_config = fires_manager.get_config_value('export', mode, default={})
    exporter = exporter_klass(extra_exports, **exporter_config)

    exporter_export(fires_manager)
