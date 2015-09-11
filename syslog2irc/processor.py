# -*- coding: utf-8 -*-

"""
syslog2irc.processor
~~~~~~~~~~~~~~~~~~~~

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from collections import defaultdict

from .runner import Runner
from .signals import irc_channel_joined, message_approved, \
    shutdown_requested, syslog_message_received
from .syslog import format_message as format_syslog_message
from .util import log


class Processor(Runner):

    def __init__(self, channel_names_to_ports):
        super(Processor, self).__init__()

        self.router = Router(channel_names_to_ports)

    def connect_to_signals(self):
        irc_channel_joined.connect(self.router.enable_channel)
        shutdown_requested.connect(self.request_shutdown)
        syslog_message_received.connect(self.handle_syslog_message)

    def handle_syslog_message(self, port, source_address=None,
            message=None):
        """Log and process an incoming syslog message."""
        source = '{0[0]}:{0[1]:d}'.format(source_address)

        log('Received message from {} on port {:d} -> {}',
            source, port, format_message_for_log(message))

        formatted_message = format_syslog_message(message)
        irc_message = '{} {}'.format(source, formatted_message)
        for channel_name in self.router.get_channel_names_for_port(port):
            message_approved.send(channel_name=channel_name,
                                  text=irc_message)


class Router(object):
    """Map IRC channel names to syslog port numbers."""

    def __init__(self, channel_names_to_ports):
        self.channel_names_to_ports = channel_names_to_ports
        self.ports_to_channel_names = defaultdict(set)

    def enable_channel(self, sender, channel=None):
        ports = self.channel_names_to_ports[channel]

        log('Enabled forwarding to channel {} from ports {}.',
            channel, ports)

        for port in ports:
            self.ports_to_channel_names[port].add(channel)

    def get_channel_names_for_port(self, port):
        return self.ports_to_channel_names[port]


def format_message_for_log(message):
    facility_name = message.facility.name
    severity_name = message.severity.name
    timestamp_str = message.timestamp.isoformat()
    hostname = message.hostname

    return 'facility={}, severity={}, timestamp={}, hostname={}, message={}' \
           .format(facility_name, severity_name, timestamp_str, hostname,
                   message.message)
