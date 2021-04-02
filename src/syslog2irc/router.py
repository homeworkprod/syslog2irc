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

    def __init__(self, ports_to_channel_names):
        self.ports_to_channel_names = ports_to_channel_names
        self.channel_names_to_ports = \
            map_channel_names_to_ports(ports_to_channel_names)
        self.enabled_channels = set()

    def enable_channel(self, sender, channel=None):
        self.enabled_channels.add(channel)
        ports = self.channel_names_to_ports[channel]
        log('Enabled forwarding to channel {} from ports {}.', channel, ports)

    def is_channel_enabled(self, channel):
        return channel in self.enabled_channels

    def get_channel_names(self):
        return frozenset(self.channel_names_to_ports.keys())

    def get_channel_names_for_port(self, port):
        return self.ports_to_channel_names[port]


def replace_channels_with_channel_names(routes):
    return {ports: channels_to_names(channels)
            for ports, channels in routes.items()}


def channels_to_names(channels):
    return {channel.name for channel in channels}


def map_channel_names_to_ports(ports_to_channel_names):
    channel_names_to_ports = defaultdict(set)
    for port, channel_names in ports_to_channel_names.items():
        for channel_name in channel_names:
            channel_names_to_ports[channel_name].add(port)
    return dict(channel_names_to_ports)
