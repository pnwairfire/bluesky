"""bluesky"""

__version_info__ = (4,3,70)
__version__ = '.'.join([str(n) for n in __version_info__])

__author__ = "Joel Dubowy"


import logging

# Adapted from https://stackoverflow.com/questions/2183233/
def add_logging_level(level_name, level_num):

    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    method_name = level_name.lower()
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)

add_logging_level('SUMMARY', 25)
