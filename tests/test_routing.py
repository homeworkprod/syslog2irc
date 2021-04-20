"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.router import map_channel_names_to_ports


@pytest.mark.parametrize(
    'routes, expected',
    [
        (
            {
                514: ['#example1'],
            },
            {
                '#example1': {514},
            },
        ),
        (
            {
                  514: ['#example1', '#example2'],
                55514: ['#example2'],
            },
            {
                '#example1': {514},
                '#example2': {514, 55514},
            },
        ),
    ],
)
def test_map_channel_names_to_ports(routes, expected):
    assert map_channel_names_to_ports(routes) == expected
