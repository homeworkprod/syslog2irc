"""
syslog2irc.irc
~~~~~~~~~~~~~~

Internet Relay Chat

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from dataclasses import dataclass
from ssl import wrap_socket as ssl_wrap_socket
from typing import List, Optional

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
    channels: List[IrcChannel]


class Bot(SingleServerIRCBot):
    """An IRC bot to forward messages to IRC channels."""

    def __init__(self, server, nickname, realname, channels):
        log('Connecting to IRC server {0.host}:{0.port:d} ...', server)

        server_spec = ServerSpec(server.host, server.port)
        factory = Factory(wrapper=ssl_wrap_socket) if server.ssl else Factory()
        SingleServerIRCBot.__init__(
            self, [server_spec], nickname, realname, connect_factory=factory
        )

        # Note: `self.channels` already exists in super class.
        self.channels_to_join = channels

    def start(self):
        """Connect to the server, in a separate thread."""
        start_thread(super().start, self.__class__.__name__)

    def get_version(self):
        """Return this on CTCP VERSION requests."""
        return 'syslog2IRC'

    def on_welcome(self, conn, event):
        """Join channels after connect."""
        log('Connected to {}:{:d}.', *conn.socket.getpeername())

        channel_names = sorted(c.name for c in self.channels_to_join)
        log('Channels to join: {}', ', '.join(channel_names))

        for channel in self.channels_to_join:
            conn.join(channel.name, channel.password or '')

    def on_nicknameinuse(self, conn, event):
        """Choose another nickname if conflicting."""
        self._nickname += '_'
        conn.nick(self._nickname)

    def on_join(self, conn, event):
        """Successfully joined channel."""
        joined_nick = event.source.nick
        channel_name = event.target

        if joined_nick == self._nickname:
            log('Joined IRC channel: {}', channel_name)
            irc_channel_joined.send(channel=channel_name)

    def on_badchannelkey(self, conn, event):
        """Channel could not be joined due to wrong password."""
        channel_name = event.arguments[0]
        log('Cannot join channel {} (bad key).', channel_name)

    def say(self, channel_name, text):
        """Say message on channel."""
        self.connection.privmsg(channel_name, text)


class DummyBot:
    def __init__(self, channels):
        self.channels = channels

    def start(self):
        # Fake channel joins.
        for channel in self.channels:
            irc_channel_joined.send(channel=channel.name)

    def say(self, channel_name, text):
        log('{}> {}', channel_name, text)
