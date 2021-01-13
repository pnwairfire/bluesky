"""bluesky.exporters.email"""

__author__ = "Joel Dubowy"

import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from bluesky.exceptions import BlueSkyConfigurationError
from . import ExporterBase

__all__ = [
    'EmailExporter'
]

__version__ = "0.1.0"

class EmailExporter(ExporterBase):

    def __init__(self, extra_exports):
        super(EmailExporter, self).__init__(extra_exports)
        self._recipients = self.config('recipients')
        if not self._recipients:
            raise BlueSkyConfigurationError("Specify email recipients.")
        # TODO: make sure each email address is valid
        self._sender = self.config('sender')
        self._subject = self.config('subject')
        self._server = self.config('smtp_server')
        self._port = int(self.config('smtp_port'))
        self._smtp_starttls = self.config('smtp_starttls')
        self._username = self.config('username')
        self._password = self.config('password')

        # TODO: read the following from config
         # - smtp_username -- no default
         # - smtp_password -- no default

    def export(self, fires_manager):
        logging.info('Sending Email to %s', self._recipients)
        fires_manager.export = fires_manager.export or {}
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self._sender
            msg['To'] = ', '.join(self._recipients)
            msg['Subject'] = self._subject

            # TODO: attach json dump of fires_manager instead of making it
            #   the email's content ?
            content = self._get_output_dump(fires_manager)

            # TODO: attach other output files according to what's in
            #   self._extra_exports

            msg.attach(MIMEText(content, 'plain'))
            msg.attach(MIMEText(content, 'html'))

            logging.debug('Connecting to SMTP server %s %s', self._server, self._port)
            s = smtplib.SMTP(self._server, self._port)

            if self._smtp_starttls:
                logging.debug('Using STARTTLS')
                s.ehlo()
                s.starttls()
                s.ehlo()

            if self._username and self._password:
                logging.debug('Logging into SMTP server with u/p')
                s.login(self._username, self._password)

            s.sendmail(msg['from'], self._recipients, msg.as_string())
            s.quit()
            fires_manager.export['email'] = {"sent_to": self._recipients}

        except Exception as e:
            msg = 'Failed to send email to {} - {}'.format(
                ', '.join(self._recipients), str(e))
            logging.error(msg)
            fires_manager.export['email'] = {"error": msg}