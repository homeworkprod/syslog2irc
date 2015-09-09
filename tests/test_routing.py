# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from unittest import TestCase

from nose2.tools import params

from syslog2irc.irc import IrcChannel
from syslog2irc.main import map_channel_names_to_ports


class RoutingTestCase(TestCase):

    irc_channel1 = IrcChannel('#example1')
    irc_channel2 = IrcChannel('#example2', password='opensesame')

    @params(
        (
            {
                514: [irc_channel1],
            },
            {
                '#example1': {514},
            },
        ),
        (
            {
                  514: [irc_channel1, irc_channel2],
                55514: [irc_channel2],
            },
            {
                '#example1': {514},
                '#example2': {514, 55514},
            },
        ),
    )
    def test_map_channel_names_to_ports(self, routes, expected):
        actual = map_channel_names_to_ports(routes)

        self.assertEqual(actual, expected)
