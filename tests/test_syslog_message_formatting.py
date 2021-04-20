"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from datetime import datetime

import pytest
from syslogmp import Facility, Message, Severity

from syslog2irc.processor import format_syslog_message


@pytest.mark.parametrize(
    'facility, severity, timestamp, hostname, message, expected',
    [
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
    ],
)
def test_format_message(
    facility, severity, timestamp, hostname, message, expected
):
    """Test string representation of a syslog message."""
    message = Message(facility, severity, timestamp, hostname, message)
    assert format_syslog_message(message) == expected
