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
        self.ports_to_channel_names = \
            map_ports_to_channel_names(channel_names_to_ports)
        self.enabled_channels = set()

    def enable_channel(self, sender, channel=None):
        self.enabled_channels.add(channel)
        ports = self.channel_names_to_ports[channel]
        log('Enabled forwarding to channel {} from ports {}.', channel, ports)

    def is_channel_enabled(self, channel):
        return channel in self.enabled_channels

    def get_channel_names_for_port(self, port):
        return self.ports_to_channel_names[port]


def map_channel_names_to_ports(routes):
    channel_names_to_ports = defaultdict(set)
    for port, channels in routes.items():
        for channel in channels:
            channel_names_to_ports[channel.name].add(port)
    return dict(channel_names_to_ports)


def map_ports_to_channel_names(channel_names_to_ports):
    ports_to_channel_names = defaultdict(set)
    for channel_name, ports in channel_names_to_ports.items():
        for port in ports:
            ports_to_channel_names[port].add(channel_name)
    return dict(ports_to_channel_names)
