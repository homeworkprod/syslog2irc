"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.network import Port, TransportProtocol
from syslog2irc.router import map_channel_names_to_ports, Router


def create_port(number):
    return Port(number, TransportProtocol.UDP)


@pytest.mark.parametrize(
    'routes, expected',
    [
        (
            {
                create_port(514): ['#example1'],
            },
            {
                '#example1': {create_port(514)},
            },
        ),
        (
            {
                create_port(514): ['#example1', '#example2'],
                create_port(55514): ['#example2'],
            },
            {
                '#example1': {create_port(514)},
                '#example2': {create_port(514), create_port(55514)},
            },
        ),
    ],
)
def test_map_channel_names_to_ports(routes, expected):
    assert map_channel_names_to_ports(routes) == expected


def test_do_not_enable_channel_without_routed_ports():
    router = Router({create_port(514): {'#one'}})

    router.enable_channel(None, channel_name='#one')
    router.enable_channel(None, channel_name='#two')

    assert router.is_channel_enabled('#one')
    assert not router.is_channel_enabled('#two')
