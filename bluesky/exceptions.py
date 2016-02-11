"""bluesky.exceptions

Defines exception classes to let calling code handle errors differently
"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2016, AirFire, PNW, USFS"

__all__ = [
    "BlueSkyImportError",
    "BlueSkyModuleError"
]

class BlueSkyImportError(ImportError):
    pass

class BlueSkyConfigurationError(ValueError):
    pass

class BlueSkyModuleError(Exception):
    pass

class InvalidFilterError(ValueError):
    pass
