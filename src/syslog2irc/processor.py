"""
syslog2irc.processor
~~~~~~~~~~~~~~~~~~~~

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import logging
from time import sleep
from typing import Callable, Optional, Set, Tuple, Union

from syslogmp import Message as SyslogMessage

from .formatting import format_message
from .config import Config
from .irc import Bot as IrcBot, create_bot, DummyBot as DummyIrcBot
from .network import Port
from .routing import map_ports_to_channel_names, Router
from .signals import irc_channel_joined, syslog_message_received
from .syslog import start_syslog_message_receivers


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
                self.irc_bot.say(channel_name, text)

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


def create_processor(config: Config) -> Processor:
    """Create a processor."""
    ports_to_channel_names = map_ports_to_channel_names(config.routes)

    irc_bot = create_bot(config.irc)
    router = Router(ports_to_channel_names)

    return Processor(irc_bot, router)
