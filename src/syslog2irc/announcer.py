"""
syslog2irc.announcer
~~~~~~~~~~~~~~~~~~~~

Message announcing

:Copyright: 2007-2021 Jochen Kupperschmidt
:License: MIT, see LICENSE for details.
"""

from .irc import Bot
from .util import log, start_thread


class IrcAnnouncer:
    """Announce syslog messages on IRC."""

    def __init__(self, server, nickname, realname, channels):
        self.bot = Bot(server, nickname, realname, channels)

    def start(self):
        start_thread(self.bot.start, 'IrcAnnouncer')

    def announce(self, sender, channel_name=None, text=None):
        self.bot.say(channel_name, text)


class StdoutAnnouncer:
    """Announce syslog messages on STDOUT."""

    def start(self):
        pass

    def announce(self, sender, channel_name=None, text=None):
        log('{}> {}', channel_name, text)


def create_announcer(config):
    """Create and return an announcer according to the configuration."""
    if config.server is None:
        log('No IRC server specified; will write to STDOUT instead.')
        return StdoutAnnouncer()

    return IrcAnnouncer(
        config.server, config.nickname, config.realname, config.channels
    )
