# -*- coding: utf-8 -*-

"""
Tests for syslog2IRC
====================


Requirements
------------

- nose2_ (tested with version 0.4.6)


Installation
------------

Install nose2_:

.. code:: sh

    $ pip install nose2


Usage
-----

Run the tests (attention: do *not* specify the `.py` extension, just the
module name!):

.. code:: sh

    $ nose2 test_syslog2irc


.. _nose2: https://github.com/nose-devs/nose2


:Copyright: 2007-2014 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:Date: 15-May-2014 (original release: 12-Apr-2007)
:License: MIT, see LICENSE for details.
:Version: 0.6
"""

from __future__ import unicode_literals
from datetime import datetime
from unittest import TestCase

from nose2.tools import params

from syslog2irc import (IrcChannel, format_syslog_message, \
    map_channel_names_to_ports, parse_irc_server_arg, SyslogFacility, \
    SyslogMessage, SyslogMessageParser, SyslogSeverity)


CURRENT_YEAR = datetime.today().year


class SyslogMessageTestCase(TestCase):

    @params(
        (
            # Example 1 from RFC 3164.
            '<34>Oct 11 22:14:15 mymachine su: \'su root\' failed for lonvick on /dev/pts/8',
            SyslogFacility.security4,
            'security/authorization messages',
            SyslogSeverity.critical,
            datetime(CURRENT_YEAR, 10, 11, 22, 14, 15),
            'mymachine',
            'su: \'su root\' failed for lonvick on /dev/pts/8',
        ),
        (
            # Example 2 from RFC 3164.
            '<13>Feb  5 17:32:18 10.0.0.99 Use the BFG!',
            SyslogFacility.user,
            'user-level messages',
            SyslogSeverity.notice,
            datetime(CURRENT_YEAR, 2, 5, 17, 32, 18),
            '10.0.0.99',
            'Use the BFG!',
        ),
        (
            # Example 3 from RFC 3164.
            # Note that the HOSTNAME and MSG fields in this example are not
            # consistent with what the RFC defines.
            '<165>Aug 24 05:34:00 CST 1987 mymachine myproc[10]: %% It\'s time to make the do-nuts.  %%  Ingredients: Mix=OK, Jelly=OK # Devices: Mixer=OK, Jelly_Injector=OK, Frier=OK # Transport: Conveyer1=OK, Conveyer2=OK # %%',
            SyslogFacility.local4,
            'local use 4 (local4)',
            SyslogSeverity.notice,
            datetime(CURRENT_YEAR, 8, 24, 5, 34, 0),
            'CST',
            '1987 mymachine myproc[10]: %% It\'s time to make the do-nuts.  %%  Ingredients: Mix=OK, Jelly=OK # Devices: Mixer=OK, Jelly_Injector=OK, Frier=OK # Transport: Conveyer1=OK, Conveyer2=OK # %%',
        ),
            # Example 4 from RFC 3164 (included for the sake of completeness).
            # This cannot be parsed because the format of the TIMESTAMP field
            # is invalid.
            #'<0>1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
        (
            # Example 5 from RFC 3164.
            '<0>Oct 22 10:52:12 scapegoat 1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
            SyslogFacility.kernel,
            'kernel messages',
            SyslogSeverity.emergency,
            datetime(CURRENT_YEAR, 10, 22, 10, 52, 12),
            'scapegoat',
            '1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
        ),
    )
    def test_syslog_message_parser(
            self,
            data,
            expected_facility,
            expected_facility_description,
            expected_severity,
            expected_timestamp,
            expected_hostname,
            expected_message):
        """Test parsing of a syslog message."""
        actual = SyslogMessageParser.parse(data)

        self.assertEqual(actual.facility, expected_facility)
        self.assertEqual(actual.facility.description, expected_facility_description)
        self.assertEqual(actual.severity, expected_severity)
        self.assertEqual(actual.timestamp, expected_timestamp)
        self.assertEqual(actual.hostname, expected_hostname)
        self.assertEqual(actual.message, expected_message)

    @params(
        (
            SyslogFacility.user,
            SyslogSeverity.informational,
            None,
            None,
            'FYI',
            '[informational]: FYI',
        ),
        (
            SyslogFacility.clock9,
            SyslogSeverity.warning,
            datetime(2013, 7, 8, 0, 12, 55),
            None,
            'Tick, tack, watch the clock!',
            '[2013-07-08 00:12:55] [warning]: Tick, tack, watch the clock!',
        ),
        (
            SyslogFacility.ntp,
            SyslogSeverity.debug,
            None,
            'ntp.local',
            'What time is it?',
            '(ntp.local) [debug]: What time is it?',
        ),
        (
            SyslogFacility.kernel,
            SyslogSeverity.emergency,
            datetime(2008, 10, 18, 17, 34, 7),
            'mainframe',
            'WTF? S.O.S.!',
            '[2008-10-18 17:34:07] (mainframe) [emergency]: WTF? S.O.S.!',
        ),
    )
    def test_format_syslog_message(self, facility, severity, timestamp,
            hostname, message, expected):
        """Test string representation of a syslog message."""
        message = SyslogMessage(facility, severity, timestamp, hostname,
            message)

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
