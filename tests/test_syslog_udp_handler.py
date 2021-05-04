"""
:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from datetime import datetime

from syslogmp import Facility, Message, Severity

from syslog2irc.network import Port, TransportProtocol
from syslog2irc.signals import syslog_message_received
from syslog2irc.syslog import UDPHandler


CURRENT_YEAR = datetime.today().year


def test_udp_handler():
    expected_message = Message(
        Facility.kernel,
        Severity.emergency,
        datetime(CURRENT_YEAR, 10, 22, 10, 52, 12),
        'scapegoat',
        b'1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
    )

    # Example 5 from RFC 3164.
    data = b'<0>Oct 22 10:52:12 scapegoat 1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!'

    port = Port(514, TransportProtocol.UDP)
    client_address = ('127.0.0.1', port.number)
    request = [data]

    received_signal_data = []

    @syslog_message_received.connect
    def handle_syslog_message_received(sender, **data):
        received_signal_data.append(data)

    UDPHandler(port, request, client_address, server=None)

    assert received_signal_data == [
        {
            'message': expected_message,
            'source_address': client_address,
        }
    ]
