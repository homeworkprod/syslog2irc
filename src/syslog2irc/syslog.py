"""
syslog2irc.syslog
~~~~~~~~~~~~~~~~~

BSD syslog message reception and handling

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from functools import partial
import logging
from socketserver import (
    BaseRequestHandler,
    StreamRequestHandler,
    ThreadingTCPServer,
    ThreadingUDPServer,
)
import sys
from typing import Iterable, Tuple, Union

import syslogmp
from syslogmp import Message as SyslogMessage

from .network import format_port, Port, TransportProtocol
from .signals import syslog_message_received
from .util import start_thread


logger = logging.getLogger(__name__)


class TCPHandler(StreamRequestHandler):
    """Handler for syslog messages arriving via TCP."""

    def __init__(self, port: Port, *args, **kwargs) -> None:
        self.port = port
        super().__init__(*args, **kwargs)

    def handle(self) -> None:
        for line in self.rfile:
            try:
                message = syslogmp.parse(line)
            except ValueError:
                logger.info(
                    'Invalid message received from %s:%d.', *self.client_address
                )
                return None

            _handle_received_message(self.client_address, self.port, message)


class UDPHandler(BaseRequestHandler):
    """Handler for syslog messages arriving via UDP."""

    def __init__(self, port: Port, *args, **kwargs) -> None:
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

        _handle_received_message(self.client_address, self.port, message)


def _handle_received_message(
    client_address: Tuple[str, int], port: Port, message: SyslogMessage
) -> None:
    logger.debug(
        'Received message from %s:%d on port %s -> %s',
        client_address[0],
        client_address[1],
        format_port(port),
        format_message_for_log(message),
    )

    syslog_message_received.send(
        port, source_address=client_address, message=message
    )


def create_server(port: Port) -> Union[ThreadingTCPServer, ThreadingUDPServer]:
    """Create a threading server to receive syslog messages."""
    address = ('', port.number)

    if port.transport_protocol == TransportProtocol.TCP:
        tcp_handler_class = partial(TCPHandler, port)
        return ThreadingTCPServer(address, tcp_handler_class)
    elif port.transport_protocol == TransportProtocol.UDP:
        udp_handler_class = partial(UDPHandler, port)
        return ThreadingUDPServer(address, udp_handler_class)
    else:
        raise ValueError(f'Unsupported transport protocol')


def start_server(port: Port) -> None:
    """Start a server, in a separate thread."""
    try:
        server = create_server(port)
    except OSError as e:
        sys.stderr.write(f'Error {e.errno:d}: {e.strerror}\n')
        sys.stderr.write(
            f'Cannot open port {format_port(port)}. Could be already in use. '
            f'Or permission is lacking; try a port number above 1,024 (or '
            'even 4,096) and up to 65,535.\n'
        )
        sys.exit(1)

    thread_name = f'{server.__class__.__name__}-port{port}'
    start_thread(server.serve_forever, thread_name)
    logger.info(
        'Listening for syslog messages on %s:%s.',
        server.server_address[0],
        format_port(port),
    )


def start_syslog_message_receivers(ports: Iterable[Port]) -> None:
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
