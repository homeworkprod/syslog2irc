"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from syslog2irc.processor import Processor
from syslog2irc.router import Router
from syslog2irc.signals import irc_channel_joined


def test_channel_enabling_on_join_signal():
    ports_to_channel_names = {
          514: {'#example1', '#example2'},
        55514: {'#example2'},
    }

    processor = create_processor(ports_to_channel_names)

    assert not processor.router.is_channel_enabled('#example1')
    assert not processor.router.is_channel_enabled('#example2')

    irc_channel_joined.send(channel_name='#example1')

    assert processor.router.is_channel_enabled('#example1')
    assert not processor.router.is_channel_enabled('#example2')

    irc_channel_joined.send(channel_name='#example2')

    assert processor.router.is_channel_enabled('#example1')
    assert processor.router.is_channel_enabled('#example2')


def create_processor(ports_to_channel_names):
    router = Router(ports_to_channel_names)

    processor = Processor(router)
    processor.connect_to_signals()
    return processor
