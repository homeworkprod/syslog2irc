"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from syslog2irc.processor import Processor
from syslog2irc.router import Router
from syslog2irc.signals import shutdown_requested


def test_shutdown_flag_set_on_shutdown_signal():
    processor = create_processor()
    assert not processor.shutdown

    shutdown_requested.send()
    assert processor.shutdown


def create_processor():
    router = Router({})

    processor = Processor(router)
    processor.connect_to_signals()
    return processor
