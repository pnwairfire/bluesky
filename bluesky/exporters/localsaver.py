# TODO: look at config>export>local>dest, which hsould be root dir to contain
#   output dir, or outputdir itself (?).  If root dir containing, then also
#   suport specifying a run_id, which is generated if not specified (could also
#   look at dispersion or visualization run_id, if they're in data)

# TODO: dump fires_manager to json (configurable dir and filename)


"""bluesky.exporters.uploader"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from . import ExporterBase

__all__ = [
    'LocalSaveExporter'
]

__version__ = "0.1.0"


class LocalSaveExporter(ExporterBase):
    pass
