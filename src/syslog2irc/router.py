"""
syslog2irc.router
~~~~~~~~~~~~~~~~~

Routing of syslog messages to IRC channels by the port they arrive on.

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from .util import log


@dataclass(frozen=True)
class Route:
    """A route from a syslog message receiver port to an IRC channel."""

    port: int
    irc_channel_name: str


class Router:
    """Map syslog port numbers to IRC channel names."""

    def __init__(self, ports_to_channel_names: Dict[int, Set[str]]) -> None:
        self.ports_to_channel_names = ports_to_channel_names
        self.channel_names_to_ports = map_channel_names_to_ports(
            ports_to_channel_names
        )
        self.enabled_channels: Set[str] = set()

    def enable_channel(
        self, sender: Any, *, channel_name: Optional[str] = None
    ) -> None:
        self.enabled_channels.add(channel_name)
        ports = self.channel_names_to_ports[channel_name]
        log(
            'Enabled forwarding to channel {} from ports {}.',
            channel_name,
            ports,
        )

    def is_channel_enabled(self, channel: str) -> bool:
        return channel in self.enabled_channels

    def get_channel_names_for_port(self, port: int) -> Set[str]:
        return self.ports_to_channel_names[port]


def map_ports_to_channel_names(routes: Set[Route]) -> Dict[int, Set[str]]:
    ports_to_channel_names = defaultdict(set)
    for route in routes:
        ports_to_channel_names[route.port].add(route.irc_channel_name)
    return dict(ports_to_channel_names)


def map_channel_names_to_ports(
    ports_to_channel_names: Dict[int, Set[str]]
) -> Dict[str, Set[int]]:
    channel_names_to_ports = defaultdict(set)
    for port, channel_names in ports_to_channel_names.items():
        for channel_name in channel_names:
            channel_names_to_ports[channel_name].add(port)
    return dict(channel_names_to_ports)
