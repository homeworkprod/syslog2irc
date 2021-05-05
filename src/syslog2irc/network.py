"""
syslog2irc.network
~~~~~~~~~~~~~~~~~~

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from dataclasses import dataclass
from enum import Enum


TransportProtocol = Enum('TransportProtocol', ['TCP', 'UDP'])


@dataclass(frozen=True, order=True)
class Port:
    """A network port."""

    number: int
    transport_protocol: TransportProtocol


def format_port(port: Port) -> str:
    """Return string representation for port."""
    return f'{port.number}/{port.transport_protocol.name.lower()}'


def parse_port(value: str) -> Port:
    """Extract port number and protocol from string representation."""
    tokens = value.split('/', maxsplit=1)
    if len(tokens) != 2:
        raise ValueError(f'Invalid port string "{value}"')

    number_str = tokens[0]
    try:
        number = int(number_str)
    except ValueError:
        raise ValueError(f'Invalid port number "{number_str}"')
    if number < 1 or number > 65535:
        raise ValueError(f'Invalid port number "{number_str}"')

    transport_protocol_str = tokens[1]
    try:
        transport_protocol = TransportProtocol[transport_protocol_str.upper()]
    except KeyError:
        raise ValueError(
            f'Unknown transport protocol "{transport_protocol_str}"'
        )

    return Port(number=number, transport_protocol=transport_protocol)
