#!/usr/bin/env python

"""
syslog2IRC
==========

Receive syslog messages via UDP and show them on IRC.

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from syslog2irc.cli import parse_args
from syslog2irc.config import load_config
from syslog2irc.main import start


def start_with_args() -> None:
    """Start the IRC bot and the syslog listen server."""
    args = parse_args()
    config = load_config(args.config_filename)

    start(config)


if __name__ == '__main__':
    start_with_args()
