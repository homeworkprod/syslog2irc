"""
syslog2irc.irc
~~~~~~~~~~~~~~

Internet Relay Chat

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from dataclasses import dataclass
from ssl import wrap_socket as ssl_wrap_socket
from typing import Any, List, Optional, Set, Union

from irc.bot import ServerSpec, SingleServerIRCBot
from irc.connection import Factory

from .signals import irc_channel_joined
from .util import log, start_thread


@dataclass(frozen=True)
class IrcServer:
    """An IRC server."""

    host: str
    port: int = 6667
    ssl: bool = False
    password: Optional[str] = None
    rate_limit: Optional[float] = None


@dataclass(frozen=True)
class IrcChannel:
    """An IRC channel with optional password."""

    name: str
    password: Optional[str] = None


@dataclass(frozen=True)
class IrcConfig:
    """An IRC bot configuration."""

    server: Optional[IrcServer]
    nickname: str
    realname: str
    channels: Set[IrcChannel]


class Bot(SingleServerIRCBot):
    """An IRC bot to forward messages to IRC channels."""

    def __init__(
        self,
        server: IrcServer,
        nickname: str,
        realname: str,
        channels: Set[IrcChannel],
    ) -> None:
        log('Connecting to IRC server {0.host}:{0.port:d} ...', server)

        server_spec = ServerSpec(server.host, server.port, server.password)
        factory = Factory(wrapper=ssl_wrap_socket) if server.ssl else Factory()
        SingleServerIRCBot.__init__(
            self, [server_spec], nickname, realname, connect_factory=factory
        )

        if server.rate_limit is not None:
            log(
                'IRC send rate limit set to {:.2f} messages per second.',
                server.rate_limit,
            )
            self.connection.set_rate_limit(server.rate_limit)
        else:
            log('No IRC send rate limit set.')

        # Note: `self.channels` already exists in super class.
        self.channels_to_join = channels

    def start(self) -> None:
        """Connect to the server, in a separate thread."""
        start_thread(super().start, self.__class__.__name__)

    def get_version(self) -> str:
        """Return this on CTCP VERSION requests."""
        return 'syslog2IRC'

    def on_welcome(self, conn, event) -> None:
        """Join channels after connect."""
        log('Connected to {}:{:d}.', *conn.socket.getpeername())

        channels = _sort_channels_by_name(self.channels_to_join)
        log('Channels to join: {}', ', '.join(c.name for c in channels))

        for channel in channels:
            log('Joining channel {} ...', channel.name)
            conn.join(channel.name, channel.password or '')

    def on_nicknameinuse(self, conn, event) -> None:
        """Choose another nickname if conflicting."""
        self._nickname += '_'
        conn.nick(self._nickname)

    def on_join(self, conn, event) -> None:
        """Successfully joined channel."""
        joined_nick = event.source.nick
        channel_name = event.target

        if joined_nick == self._nickname:
            log('Joined IRC channel: {}', channel_name)
            irc_channel_joined.send(channel_name=channel_name)

    def on_badchannelkey(self, conn, event) -> None:
        """Channel could not be joined due to wrong password."""
        channel_name = event.arguments[0]
        log('Cannot join channel {} (bad key).', channel_name)

    def say(
        self,
        sender: Optional[Any],
        *,
        channel_name: Optional[str] = None,
        text: Optional[str] = None,
    ) -> None:
        """Say message on channel."""
        self.connection.privmsg(channel_name, text)


class DummyBot:
    """A fake bot that writes messages to STDOUT."""

    def __init__(self, channels: Set[IrcChannel]) -> None:
        self.channels = channels

    def start(self) -> None:
        # Fake channel joins.
        for channel in _sort_channels_by_name(self.channels):
            irc_channel_joined.send(channel_name=channel.name)

    def say(
        self,
        sender: Optional[Any],
        *,
        channel_name: Optional[str] = None,
        text: Optional[str] = None,
    ) -> None:
        log('{}> {}', channel_name, text)

    def disconnect(self, msg: str) -> None:
        # Mimics `irc.bot.SingleServerIRCBot.disconnect`.
        log('Shutting down bot ...')


def _sort_channels_by_name(channels: Set[IrcChannel]) -> List[IrcChannel]:
    return list(sorted(channels, key=lambda c: c.name))


def create_bot(config: IrcConfig) -> Union[Bot, DummyBot]:
    """Create and return an IRC bot according to the configuration."""
    if config.server is None:
        log('No IRC server specified; will write to STDOUT instead.')
        return DummyBot(config.channels)

    return Bot(config.server, config.nickname, config.realname, config.channels)
