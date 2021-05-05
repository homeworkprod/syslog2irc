"""
syslog2irc.main
~~~~~~~~~~~~~~~

Application entry point

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from .cli import parse_args
from .config import Config, load_config
from .processor import create_processor
from .util import configure_logging


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
    processor = create_processor(config)

    # Up to this point, no signals must have been sent.
    processor.connect_to_signals()

    # Signals are allowed be sent from here on.

    syslog_ports = {route.syslog_port for route in config.routes}
    processor.run(syslog_ports)


def main() -> None:
    """Parse arguments, load configuration, and start the application."""
    args = parse_args()
    configure_logging()
    config = load_config(args.config_filename)
    start(config)


if __name__ == '__main__':
    main()
