"""
syslog2irc.config
~~~~~~~~~~~~~~~~~

Configuration loading

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Set

import rtoml

from .irc import IrcChannel, IrcConfig, IrcServer
from .router import Route
from .util import log


DEFAULT_IRC_SERVER_PORT = 6667
DEFAULT_IRC_REALNAME = 'syslog'


class ConfigurationError(Exception):
    """Indicates a configuration error."""


@dataclass(frozen=True)
class Config:
    irc: IrcConfig
    routes: Set[Route]


def load_config(path: Path) -> Config:
    """Load configuration from file."""
    data = rtoml.load(path)

    irc_config = _get_irc_config(data)
    routes = _get_routes(data, irc_config.channels)

    return Config(irc=irc_config, routes=routes)


def _get_irc_config(data: Dict[str, Any]) -> IrcConfig:
    data_irc = data['irc']

    server = _get_irc_server(data_irc)
    nickname = data_irc['bot']['nickname']
    realname = data_irc['bot'].get('realname', DEFAULT_IRC_REALNAME)
    channels = set(_get_irc_channels(data_irc))

    if not channels:
        log('Warning: No IRC channels to join have been configured.')

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
    password = data_server.get('password')
    rate_limit_str = data_server.get('rate_limit')
    rate_limit = float(rate_limit_str) if rate_limit_str else None

    return IrcServer(
        host=host, port=port, ssl=ssl, password=password, rate_limit=rate_limit
    )


def _get_irc_channels(data_irc: Any) -> Iterator[IrcChannel]:
    for channel in data_irc.get('channels', []):
        name = channel['name']
        password = channel.get('password')
        yield IrcChannel(name, password)


def _get_routes(
    data: Dict[str, Any], irc_channels: Set[IrcChannel]
) -> Set[Route]:
    data_routes = data.get('routes', {})
    if not data_routes:
        log('Warning: No routes have been configured.')

    known_irc_channel_names = {c.name for c in irc_channels}

    def iterate() -> Iterator[Route]:
        for port, irc_channel_names in data_routes.items():
            for irc_channel_name in irc_channel_names:
                if irc_channel_name not in known_irc_channel_names:
                    raise ConfigurationError(
                        f'Route target IRC channel "{irc_channel_name}" '
                        'is not configured to be joined.'
                    )

                yield Route(port=int(port), irc_channel_name=irc_channel_name)

    return set(iterate())
