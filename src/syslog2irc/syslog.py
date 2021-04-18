"""
syslog2irc.syslog
~~~~~~~~~~~~~~~~~

BSD syslog message reception and handling

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from functools import partial
from socketserver import BaseRequestHandler, ThreadingUDPServer
import sys
from typing import Iterable

import syslogmp
from syslogmp import Message as SyslogMessage

from .signals import syslog_message_received
from .util import log, start_thread


class RequestHandler(BaseRequestHandler):
    """Handler for syslog messages."""

    def __init__(self, port: int, *args, **kwargs) -> None:
        self.port = port
        super().__init__(*args, **kwargs)

    def handle(self) -> None:
        try:
            data = self.request[0]
            message = syslogmp.parse(data)
        except ValueError:
            log('Invalid message received from {}:{:d}.', *self.client_address)
            return None

        log(
            'Received message from {0[0]}:{0[1]:d} on port {1:d} -> {2}',
            self.client_address,
            self.port,
            format_message_for_log(message),
        )

        syslog_message_received.send(
            self.port, source_address=self.client_address, message=message
        )


def create_server(port: int) -> ThreadingUDPServer:
    """Create a threading UDP server to receive syslog messages."""
    address = ('', port)
    handler_class = partial(RequestHandler, port)
    return ThreadingUDPServer(address, handler_class)


def start_server(port: int) -> None:
    """Start a server, in a separate thread."""
    try:
        server = create_server(port)
    except OSError as e:
        sys.stderr.write(f'Error {e.errno:d}: {e.strerror}\n')
        sys.stderr.write(
            f'Probably no permission to open port {port:d}. '
            'Try to specify a port number above 1,024 (or even '
            '4,096) and up to 65,535.\n'
        )
        sys.exit(1)

    thread_name = f'{server.__class__.__name__}-port{port:d}'
    start_thread(server.serve_forever, thread_name)
    log('Listening for syslog messages on {}:{:d}.', *server.server_address)


def start_syslog_message_receivers(ports: Iterable[int]) -> None:
    """Start one syslog message receiving server for each port."""
    for port in ports:
        start_server(port)


def format_message_for_log(message: SyslogMessage) -> str:
    """Format a syslog message to be logged."""
    facility_name = message.facility.name
    severity_name = message.severity.name
    timestamp_str = message.timestamp.isoformat()
    hostname = message.hostname

    return (
        f'facility={facility_name}, '
        f'severity={severity_name}, '
        f'timestamp={timestamp_str}, '
        f'hostname={hostname}, '
        f'message={message.message}'
    )
