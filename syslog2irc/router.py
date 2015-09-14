# -*- coding: utf-8 -*-

"""
syslog2irc.router
~~~~~~~~~~~~~~~~~

Routing of syslog messages to IRC channels by the port they arrive on.

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from collections import defaultdict

from .util import log


class Router(object):
    """Map syslog port numbers to IRC channel names."""

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


def map_channel_names_to_ports(routes):
    channel_names_to_ports = defaultdict(set)
    for port, channels in routes.items():
        for channel in channels:
            channel_names_to_ports[channel.name].add(port)
    return channel_names_to_ports
