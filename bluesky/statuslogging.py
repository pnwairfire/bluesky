"""bluesky.statuslogging"""

__author__ = "Joel Dubowy"

import asyncio
import datetime
import logging

from pyairfire import statuslogging

__all__ = [
    'StatusLogger'
]

class StatusLogger(object):

    def __init__(self, **config): #, log_level):
        self.enabled = config && config.get('enabled')
        if self.enabled:
            # TODO: error handling to catch undefined fields
            self.sl = statuslogging.StatusLogger(
                config.get('api_endpoint'), config.get('api_key'),
                config.get('api_secret'), config.get('process'))
            self.domain = config.get('domain')
            #self.log_level = log_level

    # def __getattr__(self, name):
    #     if name in ('debug', 'info', 'warn', 'error'):

    async def _log(self, status, **fields):
        try:
            logging.debug('Submitting status log')
            sl.log(status, **fields)
            logging.debug('Submitted status log')
        except:
            logging.wanr('Failed to submit status log')

    def log(self, status, step, action):
        fields = {
            'step': step,
            'action': action,
            'timestamp': datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ'),
            'machine':  'DETERMINE MACHINE',
            'domain': self.domain
        }
        if self.enabled:
            logging.debug('Before submitting status log')
            asyncio.get_event_loop().run_until_complete(
                this._log(status, **fields))
            logging.debug('After submitting status log')
        else:
            logging.debug('Status logging disabled.')
