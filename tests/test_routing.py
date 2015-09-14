# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from unittest import TestCase

from nose2.tools import params

from syslog2irc.irc import Channel
from syslog2irc.router import map_channel_names_to_ports


class RoutingTestCase(TestCase):

    channel1 = Channel('#example1')
    channel2 = Channel('#example2', password='opensesame')

    @params(
        (
            {
                514: [channel1],
            },
            {
                '#example1': {514},
            },
        ),
        (
            {
                  514: [channel1, channel2],
                55514: [channel2],
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
