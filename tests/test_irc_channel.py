"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.irc import Channel


@pytest.mark.parametrize(
    'channel, expected_name, expected_password',
    [
        (Channel('#example'),                         '#example',      None    ),
        (Channel('#example', password=None),          '#example',      None    ),
        (Channel('#headquarters', password='secret'), '#headquarters', 'secret'),
    ],
)
def test_irc_channel_creation(channel, expected_name, expected_password):
    assert channel.name == expected_name
    assert channel.password == expected_password
