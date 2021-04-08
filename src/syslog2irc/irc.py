"""
syslog2irc.irc
~~~~~~~~~~~~~~

Internet Relay Chat

:Copyright: 2007-2015 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from collections import namedtuple
from ssl import wrap_socket as ssl_wrap_socket

from irc.bot import SingleServerIRCBot
from irc.connection import Factory

from .signals import irc_channel_joined, shutdown_requested
from .util import log


class Channel(namedtuple('Channel', 'name password')):
    """An IRC channel with optional password."""

    def __new__(cls, name, password=None):
        return super(Channel, cls).__new__(cls, name, password)


class Bot(SingleServerIRCBot):
    """An IRC bot to forward syslog messages to IRC channels."""

    def __init__(
        self,
        server_spec,
        nickname,
        realname,
        channels,
        ssl=False,
        shutdown_predicate=None,
    ):
        log('Connecting to IRC server {0.host}:{0.port:d} ...', server_spec)

        connect_params = {}
        if ssl:
            ssl_factory = Factory(wrapper=ssl_wrap_socket)
            connect_params['connect_factory'] = ssl_factory

        SingleServerIRCBot.__init__(
            self, [server_spec], nickname, realname, **connect_params
        )

        # Note: `self.channels` already exists in super class.
        self.channels_to_join = channels

        self.shutdown_predicate = shutdown_predicate

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

    def on_privmsg(self, conn, event):
        """React on private messages."""
        nickmask = event.source
        text = event.arguments[0]

        if self.shutdown_predicate is not None and self.shutdown_predicate(
            nickmask, text
        ):
            self.shutdown(nickmask)

    def shutdown(self, nickmask):
        """Shut the bot down."""
        log('Shutdown requested by {}.', nickmask)
        shutdown_requested.send()
        self.die('Shutting down.')  # Joins IRC bot thread.

    def say(self, channel, message):
        """Say message on channel."""
        self.connection.privmsg(channel, message)
