"""
syslog2irc.routing
~~~~~~~~~~~~~~~~~~

Routing of syslog messages to IRC channels by the port they arrive on.

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from collections import defaultdict
from dataclasses import dataclass
import logging
from typing import Any, Dict, Optional, Set

from .network import format_port, Port


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Route:
    """A route from a syslog message receiver port to an IRC channel."""

    syslog_port: Port
    irc_channel_name: str


class Router:
    """Map syslog port numbers to IRC channel names."""

    def __init__(self, ports_to_channel_names: Dict[Port, Set[str]]) -> None:
        self.ports_to_channel_names = ports_to_channel_names
        self.channel_names_to_ports = map_channel_names_to_ports(
            ports_to_channel_names
        )
        self.enabled_channels: Set[str] = set()

    def enable_channel(
        self, sender: Any, *, channel_name: Optional[str] = None
    ) -> None:
        ports = self.channel_names_to_ports.get(channel_name, set())
        if not ports:
            logger.warning(
                'No syslog ports routed to IRC channel %s, '
                'will not forward to it.',
                channel_name,
            )
            return

        self.enabled_channels.add(channel_name)
        logger.info(
            'Enabled forwarding to IRC channel %s from syslog port(s) %s.',
            channel_name,
            ', '.join(map(format_port, sorted(ports))),
        )

    def is_channel_enabled(self, channel: str) -> bool:
        return channel in self.enabled_channels

    def get_channel_names_for_port(self, port: Port) -> Set[str]:
        return self.ports_to_channel_names[port]


def map_ports_to_channel_names(routes: Set[Route]) -> Dict[Port, Set[str]]:
    ports_to_channel_names = defaultdict(set)
    for route in routes:
        ports_to_channel_names[route.syslog_port].add(route.irc_channel_name)
    return dict(ports_to_channel_names)


def map_channel_names_to_ports(
    ports_to_channel_names: Dict[Port, Set[str]]
) -> Dict[str, Set[Port]]:
    channel_names_to_ports = defaultdict(set)
    for port, channel_names in ports_to_channel_names.items():
        for channel_name in channel_names:
            channel_names_to_ports[channel_name].add(port)
    return dict(channel_names_to_ports)
