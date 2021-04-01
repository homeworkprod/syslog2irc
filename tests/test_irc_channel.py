"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from unittest import TestCase

from nose2.tools import params

from syslog2irc.irc import Channel


class IrcChannelTestCase(TestCase):

    @params(
        (Channel('#example'),                         '#example',      None    ),
        (Channel('#example', password=None),          '#example',      None    ),
        (Channel('#headquarters', password='secret'), '#headquarters', 'secret'),
    )
    def test_irc_channel_creation(self, channel, expected_name, expected_password):
        self.assertEqual(channel.name, expected_name)
        self.assertEqual(channel.password, expected_password)
