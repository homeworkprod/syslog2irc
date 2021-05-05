"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from datetime import datetime

import pytest
from syslogmp import Facility, Message, Severity

from syslog2irc.formatting import format_message


@pytest.mark.parametrize(
    'source_address, facility, severity, timestamp, hostname, message, expected',
    [
        (
            ('10.10.0.2', 2234),
            Facility.clock9,
            Severity.warning,
            datetime(2013, 7, 8, 0, 12, 55),
            '10.10.0.2',
            b'Tick, tack, watch the clock!',
            '10.10.0.2:2234 [2013-07-08 00:12:55] (10.10.0.2) [warning]: Tick, tack, watch the clock!',
        ),
        (
            ('10.10.0.3', 3234),
            Facility.ntp,
            Severity.debug,
            datetime(2021, 5, 4, 10, 0, 27),
            'ntp.local',
            b'What time is it?',
            '10.10.0.3:3234 [2021-05-04 10:00:27] (ntp.local) [debug]: What time is it?',
        ),
        (
            ('10.10.0.4', 4234),
            Facility.kernel,
            Severity.emergency,
            datetime(2008, 10, 18, 17, 34, 7),
            'mainframe',
            b'WTF? S.O.S.!',
            '10.10.0.4:4234 [2008-10-18 17:34:07] (mainframe) [emergency]: WTF? S.O.S.!',
        ),
        (
            # Strip leading and trailing newlines.
            ('10.10.0.5', 5234),
            Facility.user,
            Severity.informational,
            datetime(2021, 5, 4, 10, 1, 4),
            '10.10.0.5',
            b'\nIgnore my surroundings.\n',
            '10.10.0.5:5234 [2021-05-04 10:01:04] (10.10.0.5) [informational]: Ignore my surroundings.',
        ),
    ],
)
def test_format_message(
    source_address, facility, severity, timestamp, hostname, message, expected
):
    """Test string representation of a syslog message."""
    message = Message(facility, severity, timestamp, hostname, message)
    assert format_message(source_address, message) == expected
