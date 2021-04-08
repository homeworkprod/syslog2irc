"""
:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from datetime import datetime

from syslogmp import Facility, Message, Severity

from syslog2irc.signals import syslog_message_received
from syslog2irc.syslog import RequestHandler


CURRENT_YEAR = datetime.today().year


def test_handle():
    expected_message = Message(
        Facility.kernel,
        Severity.emergency,
        datetime(CURRENT_YEAR, 10, 22, 10, 52, 12),
        'scapegoat',
        b'1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!',
    )

    # Example 5 from RFC 3164.
    data = b'<0>Oct 22 10:52:12 scapegoat 1990 Oct 22 10:52:01 TZ-6 scapegoat.dmz.example.org 10.1.2.3 sched[0]: That\'s All Folks!'

    request = [data]
    client_address = ('127.0.0.1', 514)
    server = FakeServer(514)

    received_signal_data = []

    @syslog_message_received.connect
    def handle_syslog_message_received(sender, **data):
        received_signal_data.append(data)

    RequestHandler(request, client_address, server)

    assert received_signal_data == [
        {
            'message': expected_message,
            'source_address': client_address,
        }
    ]


class FakeServer:
    def __init__(self, port):
        self.port = port

    def get_port(self):
        return self.port
