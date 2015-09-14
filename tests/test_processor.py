# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from unittest import TestCase

from nose2.tools import params

from syslog2irc.processor import Processor
from syslog2irc.signals import irc_channel_joined, shutdown_requested


class ProcessorTestCase(TestCase):

    def test_shutdown_flag_set_on_shutdown_signal(self):
        processor = self._create_processor()
        self.assertEqual(processor.shutdown, False)

        shutdown_requested.send()
        self.assertEqual(processor.shutdown, True)

    def test_channel_enabling_on_join_signal(self):
        ports_to_channel_names = {
              514: {'#example1', '#example2'},
            55514: {'#example2'},
        }

        processor = self._create_processor(ports_to_channel_names)

        self.assertEqual(processor.router.is_channel_enabled('#example1'), False)
        self.assertEqual(processor.router.is_channel_enabled('#example2'), False)

        irc_channel_joined.send(channel='#example1')

        self.assertEqual(processor.router.is_channel_enabled('#example1'), True)
        self.assertEqual(processor.router.is_channel_enabled('#example2'), False)

        irc_channel_joined.send(channel='#example2')

        self.assertEqual(processor.router.is_channel_enabled('#example1'), True)
        self.assertEqual(processor.router.is_channel_enabled('#example2'), True)

    def _create_processor(self, ports_to_channel_names=None):
        processor = Processor(ports_to_channel_names or {})
        processor.connect_to_signals()
        return processor
