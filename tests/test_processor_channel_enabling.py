"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from syslog2irc.main import Processor
from syslog2irc.network import Port, TransportProtocol
from syslog2irc.routing import Route, Router
from syslog2irc.signals import irc_channel_joined


def test_channel_enabling_on_join_signal():
    routes = {
        Route(Port(514, TransportProtocol.UDP), '#example1'),
        Route(Port(514, TransportProtocol.UDP), '#example2'),
        Route(Port(55514, TransportProtocol.UDP), '#example2'),
    }

    processor = create_processor(routes)

    assert not processor.router.is_channel_enabled('#example1')
    assert not processor.router.is_channel_enabled('#example2')

    irc_channel_joined.send(channel_name='#example1')

    assert processor.router.is_channel_enabled('#example1')
    assert not processor.router.is_channel_enabled('#example2')

    irc_channel_joined.send(channel_name='#example2')

    assert processor.router.is_channel_enabled('#example1')
    assert processor.router.is_channel_enabled('#example2')


def create_processor(routes):
    irc_bot = None
    syslog_ports = set()
    router = Router(routes)

    return Processor(irc_bot, syslog_ports, router)
