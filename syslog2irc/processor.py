# -*- coding: utf-8 -*-

"""
syslog2irc.processor
~~~~~~~~~~~~~~~~~~~~

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from .runner import Runner
from .signals import irc_channel_joined, message_approved, message_received, \
    shutdown_requested, syslog_message_received
from .util import log


MESSAGE_TEXT_ENCODING = 'utf-8'


class Processor(Runner):

    def __init__(self, router, syslog_message_formatter=None):
        super(Processor, self).__init__()
        self.router = router

        if syslog_message_formatter is not None:
            self.syslog_message_formatter = syslog_message_formatter
        else:
            self.syslog_message_formatter = format_syslog_message

    def connect_to_signals(self):
        irc_channel_joined.connect(self.router.enable_channel)
        shutdown_requested.connect(self.request_shutdown)
        syslog_message_received.connect(self.handle_syslog_message)
        message_received.connect(self.handle_message)

    def handle_syslog_message(self, port, source_address=None,
            message=None):
        """Process an incoming syslog message."""
        channel_names = self.router.get_channel_names_for_port(port)

        formatted_source = '{0[0]}:{0[1]:d}'.format(source_address)
        formatted_message = self.syslog_message_formatter(message)
        text = '{} {}'.format(formatted_source, formatted_message)

        message_received.send(channel_names=channel_names,
                              text=text,
                              source_address=source_address)

    def handle_message(self, sender, channel_names=None, text=None,
                       source_address=None):
        """Process an incoming message."""
        for channel_name in channel_names:
            if self.router.is_channel_enabled(channel_name):
                message_approved.send(channel_name=channel_name,
                                      text=text)


def format_syslog_message(message):
    """Format a syslog message to be displayed on IRC."""
    def _generate():
        if message.timestamp is not None:
            timestamp_format = '%Y-%m-%d %H:%M:%S'
            formatted_timestamp = message.timestamp.strftime(
                timestamp_format)
            yield '[{}] '.format(formatted_timestamp)

        if message.hostname is not None:
            yield '({}) '.format(message.hostname)

        severity_name = message.severity.name
        # Important: The message text is a byte string.
        message_text = message.message.decode(MESSAGE_TEXT_ENCODING)
        yield '[{}]: {}'.format(severity_name, message_text)

    return ''.join(_generate())
