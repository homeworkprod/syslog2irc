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
from .syslog import format_message as format_syslog_message
from .util import log


class Processor(Runner):

    def __init__(self, router):
        super(Processor, self).__init__()
        self.router = router

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
        formatted_message = format_syslog_message(message)
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
