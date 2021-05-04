"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.network import format_port, parse_port, Port, TransportProtocol


@pytest.mark.parametrize(
    'port, expected',
    [
        (Port(514, TransportProtocol.TCP), '514/tcp'),
        (Port(514, TransportProtocol.UDP), '514/udp'),
        (Port(12514, TransportProtocol.UDP), '12514/udp'),
    ],
)
def test_format_port(port, expected):
    assert format_port(port) == expected


@pytest.mark.parametrize(
    'value, expected',
    [
        ('514/tcp', Port(514, TransportProtocol.TCP)),
        ('514/udp', Port(514, TransportProtocol.UDP)),
        ('12514/udp', Port(12514, TransportProtocol.UDP)),
    ],
)
def test_parse_port(value, expected):
    assert parse_port(value) == expected


@pytest.mark.parametrize(
    'value',
    [
        '',
        '514',
        '514/x',
        '-514/udp',
        '/tcp',
        'udp/514',
        'udp',
    ],
)
def test_parse_port_failure(value):
    with pytest.raises(ValueError):
        parse_port(value)
