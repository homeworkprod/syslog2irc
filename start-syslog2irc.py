#!/usr/bin/env python

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.

:Copyright: 2007-2015 `Jochen Kupperschmidt <http://homework.nwsnet.de/>`_
:License: MIT, see LICENSE for details.
"""

from syslog2irc.argparser import parse_args
from syslog2irc.irc import IrcChannel
from syslog2irc.main import start


def start_with_args(routes, **options):
    """Start the IRC bot and the syslog listen server.

    All arguments (except for routes) are read from the command line.
    """
    args = parse_args()

    start(args.irc_server, args.irc_nickname, args.irc_realname, routes,
          ssl=args.irc_server_ssl, **options)


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
