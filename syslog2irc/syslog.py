"""
syslog2irc.syslog
~~~~~~~~~~~~~~~~~

BSD syslog message reception and handling

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from socketserver import BaseRequestHandler, ThreadingUDPServer
import sys

import syslogmp

from .signals import syslog_message_received
from .util import log, start_thread


class RequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def handle(self):
        try:
            data = self.request[0]
            message = syslogmp.parse(data)
        except ValueError:
            log('Invalid message received from {}:{:d}.',
                *self.client_address)
            return

        port = self.server.get_port()

        log('Received message from {0[0]}:{0[1]:d} on port {1:d} -> {2}',
            self.client_address, port, format_message_for_log(message))

        syslog_message_received.send(port,
                                     source_address=self.client_address,
                                     message=message)


class ReceiveServer(ThreadingUDPServer):
    """UDP server that waits for syslog messages."""

    def __init__(self, port):
        ThreadingUDPServer.__init__(self, ('', port), RequestHandler)

    @classmethod
    def start(cls, port):
        """Start in a separate thread."""
        try:
            receiver = cls(port)
        except Exception as e:
            sys.stderr.write('Error {0.errno:d}: {0.strerror}\n'
                .format(e))
            sys.stderr.write(
                'Probably no permission to open port {}. '
                'Try to specify a port number above 1,024 (or even '
                '4,096) and up to 65,535.\n'.format(port))
            sys.exit(1)

        thread_name = '{}-port{:d}'.format(cls.__name__, port)
        start_thread(receiver.serve_forever, thread_name)

    def get_port(self):
        return self.server_address[1]


def start_syslog_message_receivers(ports):
    """Start one syslog message receiving server for each port."""
    for port in ports:
        ReceiveServer.start(port)


def format_message_for_log(message):
    """Format a syslog message to be logged."""
    facility_name = message.facility.name
    severity_name = message.severity.name
    timestamp_str = message.timestamp.isoformat()
    hostname = message.hostname

    return 'facility={}, severity={}, timestamp={}, hostname={}, message={}' \
           .format(facility_name, severity_name, timestamp_str, hostname,
                   message.message)
