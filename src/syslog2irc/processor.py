"""
syslog2irc.processor
~~~~~~~~~~~~~~~~~~~~

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import logging
from time import sleep
from typing import Any, Callable, Iterator, Optional, Set, Tuple, Union

from syslogmp import Message as SyslogMessage

from .irc import Bot as IrcBot, DummyBot as DummyIrcBot
from .network import Port
from .router import Router
from .signals import (
    irc_channel_joined,
    message_received,
    syslog_message_received,
)
from .syslog import start_syslog_message_receivers


MESSAGE_TEXT_ENCODING = 'utf-8'


logger = logging.getLogger(__name__)


class Processor:
    def __init__(
        self,
        irc_bot: Union[IrcBot, DummyIrcBot],
        router: Router,
        *,
        custom_format_message: Optional[
            Callable[[Tuple[str, int], SyslogMessage], str]
        ] = None,
    ) -> None:
        self.irc_bot = irc_bot
        self.router = router

        if custom_format_message is not None:
            self.format_message = custom_format_message
        else:
            self.format_message = format_message

    def connect_to_signals(self) -> None:
        irc_channel_joined.connect(self.router.enable_channel)
        syslog_message_received.connect(self.handle_syslog_message)

    def handle_syslog_message(
        self,
        port: Port,
        *,
        source_address: Optional[Tuple[str, int]] = None,
        message: Optional[SyslogMessage] = None,
    ) -> None:
        """Process an incoming syslog message."""
        channel_names = self.router.get_channel_names_for_port(port)
        text = self.format_message(source_address, message)

        for channel_name in channel_names:
            if self.router.is_channel_enabled(channel_name):
                message_received.send(channel_name=channel_name, text=text)

    def run(
        self, syslog_ports: Set[Port], *, seconds_to_sleep: float = 0.5
    ) -> None:
        """Start network-based components, run main loop."""
        self.irc_bot.start()
        start_syslog_message_receivers(syslog_ports)

        try:
            while True:
                sleep(seconds_to_sleep)
        except KeyboardInterrupt:
            pass

        logger.info('Shutting down ...')
        self.irc_bot.disconnect('Bye.')  # Joins bot thread.


def format_message(
    source_address: Tuple[str, int], message: SyslogMessage
) -> str:
    """Format syslog message to be displayed on IRC."""

    def _generate() -> Iterator[str]:
        yield f'{source_address[0]}:{source_address[1]:d} '

        if message.timestamp is not None:
            timestamp_format = '%Y-%m-%d %H:%M:%S'
            formatted_timestamp = message.timestamp.strftime(timestamp_format)
            yield f'[{formatted_timestamp}] '

        if message.hostname is not None:
            yield f'({message.hostname}) '

        severity_name = message.severity.name

        # Important: The message text is a byte string.
        message_text = message.message.decode(MESSAGE_TEXT_ENCODING)

        # Remove leading and trailing newlines. Those would result in
        # additional lines on IRC with the usual metadata but with an
        # empty message text.
        message_text = message_text.strip('\n')

        yield f'[{severity_name}]: {message_text}'

    return ''.join(_generate())
