import logging
import os

DEBUG = os.environ.has_key('BLUESKYWEB_DEBUG')
PORT = int(os.getenv('BLUESKYWEB_PORT', 6050))
HOST = os.getenv('BLUESKYWEB_HOST', '0.0.0.0')

LOGGING_ENABLED = os.environ.get("BLUESKYWEB_LOGGING_ENABLED", "True").lower() != 'false'
LOG_FILE = os.environ.get("BLUESKYWEB_LOG_FILE", os.path.join(os.path.dirname(__file__),
    'logs', 'bluesky-scheduler.log'))
LOG_LEVEL = logging.__getattribute__(os.environ.get("LOG_LEVEL", "INFO"))

del logging
del os
