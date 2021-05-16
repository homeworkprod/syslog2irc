"""
syslog2irc.irc
~~~~~~~~~~~~~~

Internet Relay Chat

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from __future__ import annotations
from dataclasses import dataclass
import logging
import ssl
from typing import Optional, Union

from irc.bot import ServerSpec, SingleServerIRCBot
from irc.connection import Factory

from .signals import irc_channel_joined
from .util import start_thread


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IrcServer:
    """An IRC server."""

    host: str
    port: int = 6667
    ssl: bool = False
    password: Optional[str] = None
    rate_limit: Optional[float] = None


@dataclass(frozen=True, order=True)
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
    commands: list[str]
    channels: set[IrcChannel]


class Bot(SingleServerIRCBot):
    """An IRC bot to forward messages to IRC channels."""

    def __init__(
        self,
        server: IrcServer,
        nickname: str,
        realname: str,
        commands: list[str],
        channels: set[IrcChannel],
    ) -> None:
        logger.info(
            'Connecting to IRC server %s:%d ...', server.host, server.port
        )

        server_spec = ServerSpec(server.host, server.port, server.password)
        factory = Factory(wrapper=ssl.wrap_socket) if server.ssl else Factory()
        SingleServerIRCBot.__init__(
            self, [server_spec], nickname, realname, connect_factory=factory
        )

        if server.rate_limit is not None:
            logger.info(
                'IRC send rate limit set to %.2f messages per second.',
                server.rate_limit,
            )
            self.connection.set_rate_limit(server.rate_limit)
        else:
            logger.info('No IRC send rate limit set.')

        self.commands = commands

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
        logger.info(
            'Connected to IRC server %s:%d.', *conn.socket.getpeername()
        )

        self._send_custom_commands_after_welcome(conn)
        self._join_channels(conn)

    def _send_custom_commands_after_welcome(self, conn):
        """Send custom commands after having been welcomed by the server."""
        for command in self.commands:
            conn.send_raw(command)

    def _join_channels(self, conn):
        """Join the configured channels."""
        channels = sorted(self.channels_to_join)
        logger.info('Channels to join: %s', ', '.join(c.name for c in channels))

        for channel in channels:
            logger.info('Joining channel %s ...', channel.name)
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
            logger.info('Joined IRC channel: %s', channel_name)
            irc_channel_joined.send(channel_name=channel_name)

    def on_badchannelkey(self, conn, event) -> None:
        """Channel could not be joined due to wrong password."""
        channel_name = event.arguments[0]
        logger.warning('Cannot join channel %s (bad key).', channel_name)

    def say(self, channel_name: str, text: str) -> None:
        """Say message on channel."""
        self.connection.privmsg(channel_name, text)


class DummyBot:
    """A fake bot that writes messages to STDOUT."""

    def __init__(self, channels: set[IrcChannel]) -> None:
        self.channels = channels

    def start(self) -> None:
        # Fake channel joins.
        for channel in sorted(self.channels):
            irc_channel_joined.send(channel_name=channel.name)

    def say(self, channel_name: str, text: str) -> None:
        logger.debug('%s> %s', channel_name, text)

    def disconnect(self, msg: str) -> None:
        # Mimics `irc.bot.SingleServerIRCBot.disconnect`.
        logger.info('Shutting down bot ...')


def create_bot(config: IrcConfig) -> Union[Bot, DummyBot]:
    """Create and return an IRC bot according to the configuration."""
    if config.server is None:
        logger.info('No IRC server specified; will write to STDOUT instead.')
        return DummyBot(config.channels)

    return Bot(
        config.server,
        config.nickname,
        config.realname,
        config.commands,
        config.channels,
    )
