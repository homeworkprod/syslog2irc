# -*- coding: utf-8 -*-

"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from __future__ import unicode_literals
from datetime import datetime
from unittest import TestCase

from nose2.tools import params
from syslogmp import Facility, Message, Severity

from syslog2irc.syslog import format_message


class SyslogMessageFormattingTestCase(TestCase):

    @params(
        (
            Facility.user,
            Severity.informational,
            None,
            None,
            b'FYI',
            '[informational]: FYI',
        ),
        (
            Facility.clock9,
            Severity.warning,
            datetime(2013, 7, 8, 0, 12, 55),
            None,
            b'Tick, tack, watch the clock!',
            '[2013-07-08 00:12:55] [warning]: Tick, tack, watch the clock!',
        ),
        (
            Facility.ntp,
            Severity.debug,
            None,
            'ntp.local',
            b'What time is it?',
            '(ntp.local) [debug]: What time is it?',
        ),
        (
            Facility.kernel,
            Severity.emergency,
            datetime(2008, 10, 18, 17, 34, 7),
            'mainframe',
            b'WTF? S.O.S.!',
            '[2008-10-18 17:34:07] (mainframe) [emergency]: WTF? S.O.S.!',
        ),
    )
    def test_format_message(self, facility, severity, timestamp,
            hostname, message, expected):
        """Test string representation of a syslog message."""
        message = Message(facility, severity, timestamp, hostname, message)

        actual = format_message(message)

        self.assertEqual(actual, expected)
