# -*- coding: utf-8 -*-

"""
syslog2irc.syslog
~~~~~~~~~~~~~~~~~

BSD syslog message reception and handling

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

try:
    # Python 2.x
    from SocketServer import BaseRequestHandler, ThreadingUDPServer
except ImportError:
    # Python 3.x
    from socketserver import BaseRequestHandler, ThreadingUDPServer
import sys

import syslogmp

from .signals import syslog_message_received
from .util import log, start_thread


MESSAGE_TEXT_ENCODING = 'utf-8'


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


def format_message(message):
    """Format a syslog message to be displayed."""
    def _generate():
        if message.timestamp is not None:
            timestamp_format = '%Y-%m-%d %H:%M:%S'
            formatted_timestamp = message.timestamp.strftime(
                timestamp_format)
            yield '[{}] '.format(formatted_timestamp)

        if message.hostname is not None:
            yield '({}) '.format(message.hostname)

        severity_name = message.severity.name
        # Important: The message text is a byte string.
        message_text = message.message.decode(MESSAGE_TEXT_ENCODING)
        yield '[{}]: {}'.format(severity_name, message_text)

    return ''.join(_generate())
