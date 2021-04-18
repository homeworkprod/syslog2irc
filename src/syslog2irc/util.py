"""
syslog2irc.util
~~~~~~~~~~~~~~~

Various utilities

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import logging
from threading import Thread
from typing import Any, Callable, Dict


logging.basicConfig(format='%(asctime)s | %(message)s', level=logging.INFO)


def log(message: str, *args: Any, **kwargs: Dict[str, Any]) -> None:
    """Log the message with a timestamp."""
    logging.info(message.format(*args, **kwargs))


def start_thread(target: Callable, name: str) -> None:
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name, daemon=True)
    t.start()
