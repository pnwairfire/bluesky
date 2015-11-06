"""bluesky.exporters.email"""

__author__      = "Joel Dubowy"
__copyright__   = "Copyright 2015, AirFire, PNW, USFS"

from bluesky.exceptions import BlueSkyConfigurationError
from . import ExporterBase

__all__ = [
    'EmailExporter'
]

__version__ = "0.1.0"


class EmailExporter(ExporterBase):

    # TODO: should there indeed be a default sender?
    DEFAULT_SENDER = "blueskyexporter@gmail.com"
    DEFAULT_SUBJECT = "bluesky run output"

    def __init__(self, extra_exports, **config):
        super(EmailExporter, self).__init__(extra_exports, **config)
        self._recipients = self.config('recipients')
        if not self._recipients:
            raise BlueSkyConfigurationError("Specifu")
        # TODO: make sure each email address is valid
        self._sender = self.config('sender') or self.DEFAULT_SENDER
        self._subject = self.config('subject') or self.DEFAULT_SUBJECT

    def export(self, fires_manager):
        # TODO: create email
        # TODO: attach json dump of fires_amanager to email
        # TODO: attach other output files according to what's in
        #   self._extra_exports
        raise NotImplementedError("Bluesky's EmailExporter not yet implemented")
