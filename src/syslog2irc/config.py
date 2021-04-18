"""
syslog2irc.config
~~~~~~~~~~~~~~~~~

Configuration loading

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from argparse import Namespace
from itertools import chain
from typing import Dict, List

from .irc import IrcChannel, IrcConfig


def assemble_irc_config(
    args: Namespace, routes: Dict[int, List[IrcChannel]]
) -> IrcConfig:
    """Assemble IRC configuration from command line arguments and routes."""
    unique_channels = set(chain(*routes.values()))
    ordered_channels = list(sorted(unique_channels, key=lambda c: c.name))

    return IrcConfig(
        server=args.irc_server,
        nickname=args.irc_nickname,
        realname=args.irc_realname,
        channels=ordered_channels,
    )
