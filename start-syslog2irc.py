#!/usr/bin/env python

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.

:Copyright: 2007-2021 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from syslog2irc.argparser import parse_args
from syslog2irc.config import assemble_irc_config
from syslog2irc.irc import IrcChannel
from syslog2irc.main import start


def start_with_args(routes):
    """Start the IRC bot and the syslog listen server.

    All arguments (except for routes) are read from the command line.
    """
    args = parse_args()
    irc_config = assemble_irc_config(args, routes)

    start(irc_config, routes)


if __name__ == '__main__':
    # IRC channels to join
    channel1 = IrcChannel('#examplechannel1')
    channel2 = IrcChannel('#examplechannel2', password='zePassword')

    # routing for syslog messages from the ports on which they are
    # received to the IRC channels they should be announced on
    routes = {
          514: [channel1, channel2],
        55514: [channel2],
    }

    start_with_args(routes)
