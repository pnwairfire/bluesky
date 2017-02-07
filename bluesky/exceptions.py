"""bluesky.exceptions

Defines exception classes to let calling code handle errors differently
"""

__author__ = "Joel Dubowy"

__all__ = [
    "BlueSkyImportError",
    "BlueSkyConfigurationError",
    "BlueSkyModuleError",
    "MissingDependencyError",
    "BlueSkyDatetimeValueError"
]

class BlueSkyImportError(ImportError):
    pass

class BlueSkyConfigurationError(ValueError):
    pass

class BlueSkyModuleError(Exception):
    pass

class MissingDependencyError(ValueError):
    pass

class BlueSkyDatetimeValueError(ImportError):
    pass

# TODO: rename this
class BlueSkyGeographyValueError(ImportError):
    pass
