"""bluesky.modules.export"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

__all__ = [
    'run'
]

__version__ = "0.1.0"

def run(fires_manager):
    """runs the export module

    Args:
     - fires_manager -- bluesky.models.fires.FiresManager object
    """
    # TODO: dump fires_manager to json (configurable dir and filename)
    # TODO: make configurable what's to be exported (dispersion ourput,
    #   visualization output, etc.)
    raise NotImplementedError("Bluesky 'export' module not yet implemented")
