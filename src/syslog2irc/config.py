"""
syslog2irc.config
~~~~~~~~~~~~~~~~~

Configuration loading

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

import dataclasses
from dataclasses import dataclass
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Set

import rtoml

from .irc import IrcChannel, IrcConfig, IrcServer
from .router import Route


DEFAULT_IRC_SERVER_PORT = 6667
DEFAULT_IRC_REALNAME = 'syslog'


@dataclass(frozen=True)
class Config:
    irc: IrcConfig
    routes: Set[Route]


def parse_config(path: Path, routes_dict: Dict[int, Set[IrcChannel]]) -> Config:
    """Parse configuration."""
    irc_config = _load_config(path)
    irc_config = _assemble_irc_config(irc_config, routes_dict)

    routes = _parse_routes(routes_dict)

    return Config(irc=irc_config, routes=routes)


def _load_config(path: Path) -> IrcConfig:
    """Load configuration from file."""
    data = rtoml.load(path)

    irc_config = _get_irc_config(data)

    return irc_config


def _get_irc_config(data: Dict[str, Any]) -> IrcConfig:
    data_irc = data['irc']

    server = _get_irc_server(data_irc)
    nickname = data_irc['bot']['nickname']
    realname = data_irc['bot'].get('realname', DEFAULT_IRC_REALNAME)
    channels = set()

    return IrcConfig(
        server=server,
        nickname=nickname,
        realname=realname,
        channels=channels,
    )


def _get_irc_server(data_irc: Any) -> Optional[IrcServer]:
    data_server = data_irc.get('server')
    if data_server is None:
        return None

    host = data_server.get('host')
    if not host:
        return None

    port = int(data_server.get('port', DEFAULT_IRC_SERVER_PORT))
    ssl = data_server.get('ssl', False)

    return IrcServer(host=host, port=port, ssl=ssl)


def _parse_routes(routes_dict: Dict[int, Set[IrcChannel]]) -> Set[Route]:
    """Parse a routing config into separate routes."""

    def iterate() -> Iterator[Route]:
        for port, irc_channels in routes_dict.items():
            for irc_channel in irc_channels:
                yield Route(port=port, irc_channel_name=irc_channel.name)

    return set(iterate())


def _assemble_irc_config(
    irc_config: IrcConfig, routes_dict: Dict[int, Set[IrcChannel]]
) -> IrcConfig:
    """Complete IRC configuration with channels from routing config."""
    channels = set(chain(*routes_dict.values()))
    return dataclasses.replace(irc_config, channels=channels)
