"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.irc import Bot, create_bot, DummyBot, IrcConfig, IrcServer


@pytest.mark.parametrize(
    'server, expected_type',
    [
        (IrcServer('irc.server.test'), Bot),
        (None, DummyBot),
    ],
)
def test_create_bot(server, expected_type):
    config = IrcConfig(
        server=server,
        nickname='nick',
        realname='Nick',
        channels=set(),
    )

    bot = create_bot(config)

    assert type(bot) == expected_type
