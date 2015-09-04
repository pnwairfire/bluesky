from pyairfire.applogging import applogger

from bsslib.web import config

__all__ = [
    'setup_logger',
    'get_logger'
]

def setup_logger(app):
    applogger.setup_logger(
        logger=app.logger,
        log_file=config.LOG_FILE,
        logging_enabled=config.LOGGING_ENABLED,
        log_level=config.LOG_LEVEL
    )

get_logger = applogger.get_logger
