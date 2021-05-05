"""
syslog2irc.main
~~~~~~~~~~~~~~~

Orchestration, application entry point

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import logging
from queue import SimpleQueue
from typing import Callable, Optional, Set, Tuple, Union

from syslogmp import Message as SyslogMessage

from .cli import parse_args
from .config import Config, load_config
from .formatting import format_message
from .irc import Bot as IrcBot, create_bot, DummyBot as DummyIrcBot
from .network import Port
from .routing import Router
from .signals import irc_channel_joined, syslog_message_received
from .syslog import start_syslog_message_receivers
from .util import configure_logging


logger = logging.getLogger(__name__)


# A note on threads (implementation detail):
#
# This application uses threads. Besides the main thread there is one
# thread for *each* syslog message receiver (which itself is a threading
# server!) and one thread for the (actual) IRC bot. (The dummy bot does
# not run in a separate thread.)

# Those threads are configured to be daemon threads. A Python
# application exits if no more non-daemon threads are running.
#
# For details, consult the documentation on the `threading` module that
# is part of Python's standard library.


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
        self.message_queue = SimpleQueue()

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
        self.message_queue.put((port, source_address, message))

    def announce_message(
        self,
        port: Port,
        source_address: Tuple[str, int],
        message: SyslogMessage,
    ) -> None:
        """Announce message on IRC."""
        channel_names = self.router.get_channel_names_for_port(port)
        text = self.format_message(source_address, message)

        for channel_name in channel_names:
            if self.router.is_channel_enabled(channel_name):
                self.irc_bot.say(channel_name, text)

    def run(self, syslog_ports: Set[Port]) -> None:
        """Start network-based components, run main loop."""
        self.irc_bot.start()
        start_syslog_message_receivers(syslog_ports)

        try:
            while True:
                port, source_address, message = self.message_queue.get()
                self.announce_message(port, source_address, message)
        except KeyboardInterrupt:
            pass

        logger.info('Shutting down ...')
        self.irc_bot.disconnect('Bye.')  # Joins bot thread.


def create_processor(config: Config) -> Processor:
    """Create a processor."""
    irc_bot = create_bot(config.irc)
    router = Router(config.routes)

    return Processor(irc_bot, router)


def start(config: Config) -> None:
    """Start the IRC bot and the syslog listen server(s)."""
    processor = create_processor(config)

    # Up to this point, no signals must have been sent.
    processor.connect_to_signals()

    # Signals are allowed be sent from here on.

    syslog_ports = {route.syslog_port for route in config.routes}
    processor.run(syslog_ports)


def main() -> None:
    """Parse arguments, load configuration, and start the application."""
    args = parse_args()
    config = load_config(args.config_filename)
    configure_logging(config.log_level)
    start(config)


if __name__ == '__main__':
    main()
