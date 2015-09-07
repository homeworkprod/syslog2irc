# -*- coding: utf-8 -*-

"""
Tests for syslog2IRC
====================

:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from datetime import datetime
from unittest import TestCase

from nose2.tools import params
from syslogmp import Facility, Message, Severity

from syslog2irc import (IrcChannel, format_syslog_message, irc_channel_joined,
    map_channel_names_to_ports, parse_irc_server_arg, Processor,
    shutdown_requested)


CURRENT_YEAR = datetime.today().year


class SyslogMessageTestCase(TestCase):

    @params(
        (
            Facility.user,
            Severity.informational,
            None,
            None,
            'FYI',
            '[informational]: FYI',
        ),
        (
            Facility.clock9,
            Severity.warning,
            datetime(2013, 7, 8, 0, 12, 55),
            None,
            'Tick, tack, watch the clock!',
            '[2013-07-08 00:12:55] [warning]: Tick, tack, watch the clock!',
        ),
        (
            Facility.ntp,
            Severity.debug,
            None,
            'ntp.local',
            'What time is it?',
            '(ntp.local) [debug]: What time is it?',
        ),
        (
            Facility.kernel,
            Severity.emergency,
            datetime(2008, 10, 18, 17, 34, 7),
            'mainframe',
            'WTF? S.O.S.!',
            '[2008-10-18 17:34:07] (mainframe) [emergency]: WTF? S.O.S.!',
        ),
    )
    def test_format_syslog_message(self, facility, severity, timestamp,
            hostname, message, expected):
        """Test string representation of a syslog message."""
        message = Message(facility, severity, timestamp, hostname, message)

        actual = format_syslog_message(message)

        self.assertEqual(actual, expected)


class IrcChannelTestCase(TestCase):

    @params(
        (IrcChannel('#example'),                         '#example',      None    ),
        (IrcChannel('#example', password=None),          '#example',      None    ),
        (IrcChannel('#headquarters', password='secret'), '#headquarters', 'secret'),
    )
    def test_irc_channel_creation(self, channel, expected_name, expected_password):
        self.assertEqual(channel.name, expected_name)
        self.assertEqual(channel.password, expected_password)


class ArgumentParserTestCase(TestCase):

    @params(
        ('localhost',      'localhost', 6667),
        ('127.0.0.1',      '127.0.0.1', 6667),
        ('127.0.0.1:6669', '127.0.0.1', 6669),
    )
    def test_parse_irc_server_arg(self, arg_value, expected_host, expected_port):
        actual = parse_irc_server_arg(arg_value)

        self.assertEqual(actual.host, expected_host)
        self.assertEqual(actual.port, expected_port)


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


class ProcessorTestCase(TestCase):

    def test_shutdown_flag_set_on_shutdown_signal(self):
        processor = self._create_processor()
        self.assertEqual(processor.shutdown, False)

        shutdown_requested.send()
        self.assertEqual(processor.shutdown, True)

    def test_ports_to_channel_names_mapping_extended_on_join_signal(self):
        channel_names_to_ports = {
            '#example1': {514},
            '#example2': {514, 55514},
        }

        processor = self._create_processor(
            channel_names_to_ports=channel_names_to_ports)
        self.assertEqual(processor.ports_to_channel_names, {})

        irc_channel_joined.send(channel='#example1')
        self.assertEqual(processor.ports_to_channel_names, {
            514: {'#example1'},
        })

        irc_channel_joined.send(channel='#example2')
        self.assertEqual(processor.ports_to_channel_names, {
            514: {'#example1', '#example2'},
            55514: {'#example2'},
        })

    def _create_processor(self, announcer=None,
            channel_names_to_ports=None):
        processor = Processor(announcer, channel_names_to_ports or {})
        processor.connect_to_signals()
        return processor
