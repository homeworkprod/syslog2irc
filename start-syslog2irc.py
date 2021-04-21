#!/usr/bin/env python

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from typing import Dict, Set

from syslog2irc.cli import parse_args
from syslog2irc.config import parse_config
from syslog2irc.irc import IrcChannel
from syslog2irc.main import start


def start_with_args(
    channels: Set[IrcChannel], routes_dict: Dict[int, Set[str]]
) -> None:
    """Start the IRC bot and the syslog listen server."""
    args = parse_args()
    config = parse_config(args.config_filename, channels, routes_dict)

    start(config)


if __name__ == '__main__':
    # IRC channels to join
    channels = {
        IrcChannel('#examplechannel1'),
        IrcChannel('#examplechannel2', password='zePassword'),
    }

    # routing for syslog messages from the ports on which they are
    # received to the IRC channels they should be announced on
    routes = {
          514: {'#examplechannel1', '#examplechannel2'},
        55514: {'#examplechannel2'},
    }

    start_with_args(channels, routes)
