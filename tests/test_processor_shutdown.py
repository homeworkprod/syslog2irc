"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from unittest import TestCase

from syslog2irc.processor import Processor
from syslog2irc.router import Router
from syslog2irc.signals import shutdown_requested


class ProcessorShutdownTestCase(TestCase):

    def test_shutdown_flag_set_on_shutdown_signal(self):
        processor = self._create_processor()
        self.assertEqual(processor.shutdown, False)

        shutdown_requested.send()
        self.assertEqual(processor.shutdown, True)

    def _create_processor(self):
        router = Router({})

        processor = Processor(router)
        processor.connect_to_signals()
        return processor
