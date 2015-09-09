# -*- coding: utf-8 -*-

"""
syslog2irc.util
~~~~~~~~~~~~~~~

Utilities

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from __future__ import print_function
from datetime import datetime
from threading import Thread


def log(message, *args, **kwargs):
    """Log the message with a timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(timestamp, message.format(*args, **kwargs))


def start_thread(target, name):
    """Create, configure, and start a new thread."""
    t = Thread(target=target, name=name)
    t.daemon = True
    t.start()
