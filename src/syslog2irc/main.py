"""
syslog2irc.main
~~~~~~~~~~~~~~~

Application entry point

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from .cli import parse_args
from .config import Config, load_config
from .irc import create_bot
from .processor import Processor
from .router import map_ports_to_channel_names, Router
from .signals import message_approved
from .syslog import start_syslog_message_receivers


# A note on threads (implementation detail):
#
# This application uses threads. Besides the main thread there is one
# thread for *each* syslog message receiver (which itself is a
# `ThreadingUDPServer`!) and one thread for the (actual) IRC bot. (The
# dummy bot does not run in a separate thread.)

# Those threads are configured to be daemon threads. A Python
# application exits if no more non-daemon threads are running.
#
# For details, consult the documentation on the `threading` module that
# is part of Python's standard library.


def start(config: Config) -> None:
    """Start the IRC bot and the syslog listen server(s)."""
    ports = {route.port for route in config.routes}
    ports_to_channel_names = map_ports_to_channel_names(config.routes)

    irc_bot = create_bot(config.irc)
    message_approved.connect(irc_bot.say)

    router = Router(ports_to_channel_names)
    processor = Processor(router)

    # Up to this point, no signals must have been sent.
    processor.connect_to_signals()

    # Signals are allowed be sent from here on.

    start_syslog_message_receivers(ports)
    irc_bot.start()

    processor.run()

    irc_bot.disconnect('Bye.')  # Joins bot thread.


def main() -> None:
    """Parse arguments, load configuration, and start the application."""
    args = parse_args()
    config = load_config(args.config_filename)
    start(config)


if __name__ == '__main__':
    main()
