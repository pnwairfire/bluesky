"""bluesky.exceptions

Defines exception classes to let calling code handle errors differently
"""

import logging
import traceback

__author__ = "Joel Dubowy"

__all__ = [
    "BlueSkyInputError",
    "BlueSkyImportError",
    "BlueSkyConfigurationError",
    "BlueSkyModuleError",
    "MissingDependencyError",
    "BlueSkyDatetimeValueError",
    'BlueSkyGeographyValueError',
    'BlueSkyUnavailableResourceError',
    'BlueSkySubprocessError'
]

class BlueSkyInputError(RuntimeError):
    pass

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

class BlueSkyUnavailableResourceError(ValueError):
    pass

class BlueSkySubprocessError(RuntimeError):
    pass


class skip_failures():
    """Context manager that, if enabled, suppresses exceptions and
    logs the error, allowing run to continue.
    """

    def __init__(self, enabled):
        self._enabled = enabled

    def __enter__(self):
        pass

    def __exit__(self, e_type, value, tb):
        if e_type:
            if self._enabled:
                logging.warn("Skipping failure: %s", value)
                return True

            logging.debug(traceback.format_exc())
