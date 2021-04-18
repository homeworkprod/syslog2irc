"""
syslog2irc.processor
~~~~~~~~~~~~~~~~~~~~

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from time import sleep
from typing import Any, Callable, Iterator, Optional, Set, Tuple

from syslogmp import Message as SyslogMessage

from .router import Router
from .signals import (
    irc_channel_joined,
    message_approved,
    message_received,
    syslog_message_received,
)
from .util import log


MESSAGE_TEXT_ENCODING = 'utf-8'


class Processor:
    def __init__(
        self,
        router: Router,
        syslog_message_formatter: Optional[
            Callable[[SyslogMessage], str]
        ] = None,
    ) -> None:
        super(Processor, self).__init__()
        self.router = router

        if syslog_message_formatter is not None:
            self.syslog_message_formatter = syslog_message_formatter
        else:
            self.syslog_message_formatter = format_syslog_message

    def connect_to_signals(self) -> None:
        irc_channel_joined.connect(self.router.enable_channel)
        syslog_message_received.connect(self.handle_syslog_message)
        message_received.connect(self.handle_message)

    def handle_syslog_message(
        self,
        port: int,
        source_address: Optional[Tuple[str, int]] = None,
        message: Optional[SyslogMessage] = None,
    ) -> None:
        """Process an incoming syslog message."""
        channel_names = self.router.get_channel_names_for_port(port)

        formatted_source = f'{source_address[0]}:{source_address[1]:d}'
        formatted_message = self.syslog_message_formatter(message)
        text = f'{formatted_source} {formatted_message}'

        message_received.send(
            channel_names=channel_names,
            text=text,
            source_address=source_address,
        )

    def handle_message(
        self,
        sender: Any,
        *,
        channel_names: Optional[Set[str]] = None,
        text: Optional[str] = None,
        source_address: Optional[Tuple[str, int]] = None,
    ) -> None:
        """Process an incoming message."""
        for channel_name in channel_names:
            if self.router.is_channel_enabled(channel_name):
                message_approved.send(channel_name=channel_name, text=text)

    def run(self, seconds_to_sleep: float = 0.5) -> None:
        """Run the main loop."""
        try:
            while True:
                sleep(seconds_to_sleep)
        except KeyboardInterrupt:
            pass

        log('Shutting down ...')


def format_syslog_message(message: SyslogMessage) -> str:
    """Format a syslog message to be displayed on IRC."""

    def _generate() -> Iterator[str]:
        if message.timestamp is not None:
            timestamp_format = '%Y-%m-%d %H:%M:%S'
            formatted_timestamp = message.timestamp.strftime(timestamp_format)
            yield f'[{formatted_timestamp}] '

        if message.hostname is not None:
            yield f'({message.hostname}) '

        severity_name = message.severity.name
        # Important: The message text is a byte string.
        message_text = message.message.decode(MESSAGE_TEXT_ENCODING)
        yield f'[{severity_name}]: {message_text}'

    return ''.join(_generate())
