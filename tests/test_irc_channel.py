"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.irc import IrcChannel


@pytest.mark.parametrize(
    'channel, expected_name, expected_password',
    [
        (IrcChannel('#example'),                         '#example',      None    ),
        (IrcChannel('#example', password=None),          '#example',      None    ),
        (IrcChannel('#headquarters', password='secret'), '#headquarters', 'secret'),
    ],
)
def test_irc_channel_creation(channel, expected_name, expected_password):
    assert channel.name == expected_name
    assert channel.password == expected_password
