"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import pytest

from syslog2irc.irc import create_bot, IrcChannel, IrcConfig
from syslog2irc.signals import irc_channel_joined


@pytest.fixture
def config():
    channels = {IrcChannel('#one'), IrcChannel('#two')}

    return IrcConfig(
        server=None,
        nickname='nick',
        realname='Nick',
        channels=channels,
    )


@pytest.fixture
def bot(config):
    bot = create_bot(config)

    yield bot

    bot.disconnect('Done.')


def test_fake_channel_joins(bot):
    received_signal_data = []

    @irc_channel_joined.connect
    def handle_irc_channel_joined(sender, **data):
        received_signal_data.append(data)

    bot.start()

    assert received_signal_data == [
        {'channel_name': '#one'},
        {'channel_name': '#two'},
    ]
