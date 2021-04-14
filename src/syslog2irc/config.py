"""
syslog2irc.config
~~~~~~~~~~~~~~~~~

Configuration loading

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from itertools import chain

from .irc import IrcConfig


def assemble_irc_config(args, routes):
    """Assemble IRC configuration from command line arguments and routes."""
    channels = list(chain(*routes.values()))

    return IrcConfig(
        server=args.irc_server,
        nickname=args.irc_nickname,
        realname=args.irc_realname,
        channels=channels,
    )
