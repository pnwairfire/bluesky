"""bluesky.statuslogging"""

__author__ = "Joel Dubowy"

import asyncio
import datetime
import logging

from pyairfire import statuslogging

from bluesky.datetimeutils import parse_datetime

__all__ = [
    'StatusLogger'
]

class StatusLogger():

    def __init__(self, init_time, **config): #, log_level):
        self.enabled = config and config.get('enabled')
        if self.enabled:
            # parse to datetime if necessary and then format appropriately
            self.init_time = parse_datetime(init_time).strftime('%Y%m%d%H')

            # TODO: error handling to catch undefined fields
            self.sl = statuslogging.StatusLogger(
                config.get('api_endpoint'), config.get('api_key'),
                config.get('api_secret'), config.get('process'))
            self.domain = config.get('domain')
            #self.log_level = log_level

    # def __getattr__(self, name):
    #     if name in ('debug', 'info', 'warn', 'error'):

    def _log_async(self, status, **fields):
        def error_handler(e):
            logging.warning('Failed to submit status log: %s', e)

        def _log():
            # We don't need to catch exceptions here, but if we don't,
            # the failures are silent.
            try:
                self.sl.log(status, error_handler=error_handler, **fields)
                logging.debug('Submitted status log: %s', fields)
            except Exception as e:
                logging.warning('Failed to submit status log: %s', e)

        try:
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, _log)

        except Exception as e:
            logging.warning('Failed to asynchronously submit status log: %s', e)

    def log(self, status, step, action, **extra_fields):
        if self.enabled:
            ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%S.%fZ')
            fields = {
                'initialization_time': self.init_time,
                'status': status,
                'step': step,
                'action': action,
                'timestamp': ts,
                'domain': self.domain
            }
            fields.update(extra_fields)
            logging.debug("Aboout to log status: %s %s %s %s",
                status, step, action, extra_fields)
            self._log_async(**fields)
        else:
            logging.debug("Status logging disabled - not submitting "
                "'%s','%s', '%s', %s.", status, step, action, extra_fields)
