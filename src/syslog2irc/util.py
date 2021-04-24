"""
syslog2irc.util
~~~~~~~~~~~~~~~

Various utilities

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import logging
from logging import Formatter, StreamHandler
from threading import Thread
from typing import Callable


def configure_logging() -> None:
    """Configure application-specific loggers.

    Setting the log level does not affect dependencies' loggers.
    """
    # Get the parent logger of all application-specific
    # loggers defined in the package's modules.
    pkg_logger = logging.getLogger(__package__)

    # Configure handler that writes to STDERR.
    handler = StreamHandler()
    handler.setFormatter(Formatter('%(asctime)s %(levelname)-8s %(message)s'))
    pkg_logger.addHandler(handler)

    pkg_logger.setLevel(logging.DEBUG)


def start_thread(target: Callable, name: str) -> None:
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name, daemon=True)
    t.start()
