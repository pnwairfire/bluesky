"""bluesky.filtermerge"""

__author__ = "Joel Dubowy"

import abc
import logging

from bluesky.config import Config


class FiresActionBase(object, metaclass=abc.ABCMeta):
    """Base class for merging or filtering fires
    """

    def __init__(self, fires_manager, fire_class):
        """Constructor

        args:
         - fires_manager -- FiresManager object whose fires are to be merged
         - fire_class -- Fire class to instantiate new fire objects
        """
        self._fires_manager = fires_manager
        self._fire_class = fire_class
        self._skip_failures = not not Config.get(self.ACTION, 'skip_failures')

    def __enter__(self):
        logging.info("Number of fires before running %s: %s", self.ACTION,
            self._fires_manager.num_fires)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        logging.info("Number of fires after running %s: %s", self.ACTION,
            self._fires_manager.num_fires)
    ##
    ## Abstract methods
    ##

    @abc.abstractmethod
    #@property
    def _action(self):
        pass

    @abc.abstractmethod
    #@property
    def _error_class(self):
        pass

    ##
    ## Helper methods
    ##

    def _fail_fire(self, fire, sub_msg):
        msg = "Failed to {} fire {} ({}): {}".format(
            self.ACTION, fire.id, fire._private_id, sub_msg)
        raise self._error_class(msg)

    def _fail_or_skip(self, msg):
        if self._skip_failures:
            logging.warning(msg)
            return
        else:
            raise self._error_class(msg)
