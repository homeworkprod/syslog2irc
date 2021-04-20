"""
syslog2irc.config
~~~~~~~~~~~~~~~~~

Configuration loading

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from argparse import Namespace
from dataclasses import dataclass
from itertools import chain
from typing import Dict, Iterator, Set

from .irc import IrcChannel, IrcConfig
from .router import Route


@dataclass(frozen=True)
class Config:
    irc: IrcConfig
    routes: Set[Route]


def parse_config(
    args: Namespace, routes_dict: Dict[int, Set[IrcChannel]]
) -> Config:
    """Parse configuration."""
    irc_config = _assemble_irc_config(args, routes_dict)
    routes = _parse_routes(routes_dict)

    return Config(irc=irc_config, routes=routes)


def _parse_routes(routes_dict: Dict[int, Set[IrcChannel]]) -> Set[Route]:
    """Parse a routing config into separate routes."""

    def iterate() -> Iterator[Route]:
        for port, irc_channels in routes_dict.items():
            for irc_channel in irc_channels:
                yield Route(port=port, irc_channel_name=irc_channel.name)

    return set(iterate())


def _assemble_irc_config(
    args: Namespace, routes_dict: Dict[int, Set[IrcChannel]]
) -> IrcConfig:
    """Assemble IRC configuration from command line arguments and routing config."""
    channels = set(chain(*routes_dict.values()))

    return IrcConfig(
        server=args.irc_server,
        nickname=args.irc_nickname,
        realname=args.irc_realname,
        channels=channels,
    )
