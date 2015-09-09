# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from unittest import TestCase

from nose2.tools import params

from syslog2irc.irc import IrcChannel


class IrcChannelTestCase(TestCase):

    @params(
        (IrcChannel('#example'),                         '#example',      None    ),
        (IrcChannel('#example', password=None),          '#example',      None    ),
        (IrcChannel('#headquarters', password='secret'), '#headquarters', 'secret'),
    )
    def test_irc_channel_creation(self, channel, expected_name, expected_password):
        self.assertEqual(channel.name, expected_name)
        self.assertEqual(channel.password, expected_password)
