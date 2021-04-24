"""
syslog2irc.syslog
~~~~~~~~~~~~~~~~~

BSD syslog message reception and handling

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from functools import partial
import logging
from socketserver import BaseRequestHandler, ThreadingUDPServer
import sys
from typing import Iterable

import syslogmp
from syslogmp import Message as SyslogMessage

from .signals import syslog_message_received
from .util import start_thread


logger = logging.getLogger(__name__)


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
            logger.info(
                'Invalid message received from %s:%d.', *self.client_address
            )
            return None

        logger.debug(
            'Received message from %s:%d on port %d -> %s',
            self.client_address[0],
            self.client_address[1],
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
    logger.info(
        'Listening for syslog messages on %s:%d.', *server.server_address
    )


def start_syslog_message_receivers(ports: Iterable[int]) -> None:
    """Start one syslog message receiving server for each port."""
    for port in ports:
        start_server(port)


def format_message_for_log(message: SyslogMessage) -> str:
    """Format a syslog message to be logged."""
    return (
        f'facility={message.facility.name}, '
        f'severity={message.severity.name}, '
        f'timestamp={message.timestamp.isoformat()}, '
        f'hostname={message.hostname}, '
        f'message={message.message}'
    )
