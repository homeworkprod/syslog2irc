"""
syslog2irc.main
~~~~~~~~~~~~~~~

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from .announcer import create_announcer
from .processor import Processor
from .router import replace_channels_with_channel_names, Router
from .signals import message_approved
from .syslog import start_syslog_message_receivers
from .util import log


# A note on threads (implementation detail):
#
# This tool uses threads. Besides the main thread, there are two
# additional threads: one for the syslog message receiver and one for
# the IRC bot. Both are configured to be daemon threads.
#
# A Python application exits if no more non-daemon threads are running.
#
# In order to exit syslog2IRC when shutdown is requested on IRC, the IRC
# bot will call `die()`, which will join the IRC bot thread. The main
# thread and the (daemonized) syslog message receiver thread remain.
#
# Additionally, a dedicated signal is sent that sets a flag that causes
# the main loop to stop. As the syslog message receiver thread is the
# only one left, but runs as a daemon, the application exits.
#
# The STDOUT announcer, on the other hand, does not run in a thread. The
# user has to manually interrupt the application to exit.
#
# For details, see the documentation on the `threading` module that is
# part of Python's standard library.


def start(irc_config, routes):
    """Start the IRC bot and the syslog listen server."""
    try:
        ports = routes.keys()
        ports_to_channel_names = replace_channels_with_channel_names(routes)

        announcer = create_announcer(irc_config)
        message_approved.connect(announcer.announce)

        router = Router(ports_to_channel_names)
        processor = Processor(router)

        # Up to this point, no signals must have been sent.
        processor.connect_to_signals()

        # Signals are allowed be sent from here on.

        start_syslog_message_receivers(ports)
        announcer.start()

        processor.run()
    except KeyboardInterrupt:
        log('<Ctrl-C> pressed, aborting.')
