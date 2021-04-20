"""
syslog2irc.main
~~~~~~~~~~~~~~~

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from typing import Dict, Set

from .irc import create_bot, IrcChannel, IrcConfig
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
# The dummy IRC bot that writes to STDOUT, on the other hand, does not
# run in a thread. The user has to manually interrupt the application to
# exit.
#
# For details, see the documentation on the `threading` module that is
# part of Python's standard library.


def start(irc_config: IrcConfig, routes: Dict[int, Set[IrcChannel]]) -> None:
    """Start the IRC bot and the syslog listen server."""
    try:
        ports = routes.keys()
        ports_to_channel_names = replace_channels_with_channel_names(routes)

        irc_bot = create_bot(irc_config)
        message_approved.connect(irc_bot.say)

        router = Router(ports_to_channel_names)
        processor = Processor(router)

        # Up to this point, no signals must have been sent.
        processor.connect_to_signals()

        # Signals are allowed be sent from here on.

        start_syslog_message_receivers(ports)
        irc_bot.start()

        processor.run()
    except KeyboardInterrupt:
        log('<Ctrl-C> pressed, aborting.')
